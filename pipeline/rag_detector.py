import asyncio
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.sql import text
from database.session import MainSessionLocal
from database.models import AnalysisTask, RAGResult
from database.crud import update_task_status
import time
from PySide6.QtCore import QObject, Signal, QThreadPool, QRunnable, Slot
from pipeline.langchain_amayesh import DatabaseConnector, SQLQueryGenerator, ResponseGenerator, get_table_schema
import threading

class RAGWorker(QRunnable):
    def __init__(self, detector, db, task_id, prompt, user_id):
        super().__init__()
        self.detector = detector
        self.db = db
        self.task_id = task_id
        self.prompt = prompt
        self.user_id = user_id
        
    @Slot()
    def run(self):
        try:
            # Step 1: Generate SQL query using test_001 SQL generator
            log_data = {
                "type": "chatlog", 
                "state": "notif", 
                "message": "🔍 Analyzing the question and generating the SQL query..."
            }
            self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)
            
            sql_query = self.detector.sql_generator.generate_sql(self.prompt, self.detector.table_schema)
            
            log_data = {
                "type": "chatlog",
                "state": "notif", 
                "message": f"✅ The query is generated",
                "data": sql_query
            }
            self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)
            print("SQL Query : \n", sql_query)

            # Step 2: Execute SQL query using test_001 database connector
            log_data = {
                "type": "chatlog",
                "state": "notif", 
                "message": "⚡ Executing the query..."
            }
            self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)
            
            results = self.detector.db_connector.execute_query(sql_query)
            
            log_data = {
                "type": "chatlog", 
                "state": "notif", 
                "message": f"✅ {len(results)} records found"
            }
            self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)
            
            if not results:
                log_data = {
                    "type": "chatlog", 
                    "state": "warnning", 
                    "message": "⚠️ No data was found for your question."
                }
                self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)
                update_task_status(self.db, self.task_id, "completed", "No data found")
                return

            # Step 3: Show sample results (first 5)
            if len(results) > 0:
                sample_results = "\n".join([f"{i+1}. {str(row)}" for i, row in enumerate(results[:5])])
                log_data = {
                    "type": "chatlog", 
                    "state": "notif", 
                    "message": f"📊 Sample results",
                    "data": sample_results
                }
                self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)

            # Step 4: Generate final response using test_001 response generator
            log_data = {
                "type": "chatlog", 
                "state": "notif", 
                "message": "🤖 Generating the final answer..."
            }
            self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)
            
            final_response = self.detector.response_generator.generate_response(self.prompt, results, sql_query)
            
            # Step 5: Store results
            self.detector.store_results(self.db, self.task_id, self.prompt, final_response, results, self.user_id)
            
            # Send final result
            log_data = {
                "type": "chatlog", 
                "state": "Success", 
                "message": f"✅ Processing completed!",
                "data": final_response
            }
            self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)
            
            update_task_status(self.db, self.task_id, "completed", "Success")
            
        except Exception as e:
            print(f"Error processing RAG task {self.task_id}: {str(e)}")
            error_msg = f"Error in processing: {str(e)}"
            
            log_data = {
                "type": "chatlog",
                "state": "error",
                "message": error_msg
            }
            self.detector.send_log_to_user_async(self.user_id, self.task_id, log_data)
            
            update_task_status(self.db, self.task_id, "failed", error_msg)
            
        finally:
            self.db.close()

class EnhancedRAGDetector(QObject):
    log_signal = Signal(int, dict)
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
        # Initialize components from test_001
        self.db_connector = DatabaseConnector()
        self.sql_generator = SQLQueryGenerator()
        self.response_generator = ResponseGenerator()
        self.table_schema = get_table_schema()
        self.thread_pool = QThreadPool.globalInstance()

    def send_log_to_user_async(self, user_id: int, task_id: int, log_data: Dict):
        try:
            if 'taskId' not in log_data:
                log_data['taskId'] = task_id

            if 'timestamp' not in log_data:
                log_data['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')

            self.log_signal.emit(user_id, log_data)
            # await self.app_manager.send_dict_to_user_async(user_id, log_data)
        except Exception as e:
            print(f"Failed to send log to user {user_id}: {log_data}")
            print(f"Error: {str(e)}")

    def store_results(self, db, task_id: int, prompt: str, answer: str, results: List[Dict], user_id: int):
        """Store RAG results in database"""
        try:
            # Convert results to JSON string for storage
            results_json = json.dumps(results, ensure_ascii=False)
            
            # Create RAG result entry
            rag_result = RAGResult(
                task_id=task_id,
                user_id=user_id,
                prompt=prompt,
                answer=answer,
                raw_data=results_json,
                status="completed"
            )
            
            db.add(rag_result)
            db.commit()
            
        except Exception as e:
            print(f"Error storing results: {str(e)}")
            db.rollback()

    def process_task(self, task_id: int):
        """Process RAG task asynchronously using thread pool"""
        db = MainSessionLocal()

        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            print(f"Task {task_id} not found")
            return

        user_id = task.user_id
        prompt = task.data.get('prompt', '')

        # Update task status to processing immediately
        update_task_status(db, task_id, "processing")
        
        # Create worker and run it in thread pool
        worker = RAGWorker(self, db, task_id, prompt, user_id)
        self.thread_pool.start(worker)
        
        # Return immediately - the worker will handle the rest asynchronously
        return {"status": "started", "task_id": task_id}

        # db = MainSessionLocal()
        # try:
        #     # Get task information
        #     task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        #     if not task:
        #         print(f"Task {task_id} not found")
        #         return

        #     user_id = task.user_id
        #     prompt = task.data.get('prompt', '')
            
        #     if not prompt:
        #         print(f"No prompt found for task {task_id}")
        #         return

        #     # Update task status
        #     update_task_status(db, task_id, "processing")

        #     # Step 1: Generate SQL query using test_001 SQL generator
        #     log_data = {
        #         "type": "chatlog", 
        #         "state": "notif", 
        #         "message": "🔍 Analyzing the question and generating the SQL query..."
        #         }
        #     self.send_log_to_user_async(user_id, task_id, log_data)
            
        #     sql_query = self.sql_generator.generate_sql(prompt, self.table_schema)
            
        #     log_data = {
        #         "type": "chatlog",
        #         "state": "notif", 
        #         "message": f"✅ The query is generated",
        #         "data":sql_query
        #         }
        #     self.send_log_to_user_async(user_id, task_id, log_data)
        #     print ("SQL Query : \n", sql_query)

        #     # Step 2: Execute SQL query using test_001 database connector
        #     log_data = {
        #         "type": "chatlog",
        #         "state": "notif", 
        #         "message": "⚡ Executing the query..."
        #         }
        #     self.send_log_to_user_async(user_id, task_id, log_data)
            
        #     results = self.db_connector.execute_query(sql_query)
            
        #     log_data = {
        #         "type": "chatlog", 
        #         "state": "notif", 
        #         "message": f"✅ {len(results)} records found"
        #     }
        #     self.send_log_to_user_async(user_id, task_id, log_data)

        #     if not results:
        #         log_data = {
        #             "type": "chatlog", 
        #             "state": "warnning", 
        #             "message": "⚠️ No data was found for your question."
        #         }
        #         self.send_log_to_user_async(user_id, task_id, log_data)
        #         update_task_status(db, task_id, "completed", "No data found")
        #         return

        #     # Step 3: Show sample results (first 5)
        #     if len(results) > 0:
        #         sample_results = "\n".join([f"{i+1}. {str(row)}" for i, row in enumerate(results[:5])])
        #         log_data = {
        #             "type": "chatlog", 
        #             "state": "notif", 
        #             "message": f"📊 Sample results",
        #             "data":sample_results
        #         }
        #         self.send_log_to_user_async(user_id, task_id, log_data)

        #     # Step 4: Generate final response using test_001 response generator
        #     log_data = {
        #         "type": "chatlog", 
        #         "state": "notif", 
        #         "message": "🤖 Generating the final answer..."
        #         }
        #     self.send_log_to_user_async(user_id, task_id, log_data)
            
        #     final_response = self.response_generator.generate_response(prompt, results, sql_query)
            
        #     # Step 5: Store results
        #     self.store_results(db, task_id, prompt, final_response, results, user_id)
            
        #     # Send final result
        #     log_data = {
        #         "type": "chatlog", 
        #         "state": "Success", 
        #         "message": f"✅ Processing completed!",
        #         "data":final_response
        #     }
        #     self.send_log_to_user_async(user_id, task_id, log_data)
            
        #     update_task_status(db, task_id, "completed", "Success")
            
        # except Exception as e:
        #     print(f"Error processing RAG task {task_id}: {str(e)}")
        #     error_msg = f"Error in processing: {str(e)}"
            
        #     log_data = {
        #         "type": "chatlog",
        #         "state":"error",
        #         "message": error_msg
        #         }
        #     self.send_log_to_user_async(user_id, task_id, log_data)
            
        #     update_task_status(db, task_id, "failed", error_msg)
            
        # finally:
        #     db.close()

    def store_results(self, db, task_id: int, prompt: str, answer: str, results: List[Dict], user_id: int):
        """Store RAG results in database with correct field names"""
        try:
            # Convert results to JSON string for storage
            results_json = json.dumps(results, ensure_ascii=False)
            
            # Create RAG result entry with correct field names
            rag_result = RAGResult(
                task_id=task_id,
                user_id=user_id,           # Use user_id if your model has this field
                question=prompt,           # Use 'question' (not 'prompt')
                context=results_json,      # Use 'context' (not 'context_data')
                answer=answer,
                relevant_data_count=len(results)
            )
            
            db.add(rag_result)
            db.commit()
            
        except Exception as e:
            print(f"Error storing RAG results: {str(e)}")
            db.rollback()