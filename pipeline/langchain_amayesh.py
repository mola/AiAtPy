import os
from typing import List, Dict, Any
import psycopg2
from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
import json

class SQLOutputParser(BaseOutputParser):
    """Parse SQL query from LLM output"""

    def parse(self, text: str) -> str:
        # Extract SQL query from the text
        if "```sql" in text:
            text = text.split("```sql")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return text

class DatabaseConnector:
    """Handles database connection and query execution"""

    def __init__(self, dbname="diar", user="postgres", host="localhost", password=""):
        self.connection_params = {
            "dbname": dbname,
            "user": user,
            "host": host,
            "password": password
        }

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dictionaries"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()

            cursor.execute(query)

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch all results
            results = cursor.fetchall()

            # Convert to list of dictionaries
            data = []
            for row in results:
                data.append(dict(zip(columns, row)))

            cursor.close()
            conn.close()

            return data

        except Exception as e:
            print(f"Database error: {e}")
            return []

class SQLQueryGenerator:
    """Generates SQL queries using LLM"""

    def __init__(self):
        self.llm = Ollama(model="llama3.1")
        self.prompt_template = PromptTemplate(
            input_variables=["question", "table_schema"],
            template="""
            شما یک دستیار هوشمند برای تولید کوئری SQL هستید. بر اساس سوال کاربر و ساختار جدول، کوئری SQL مناسب تولید کنید.

            ساختار جدول amayesh:
            {table_schema}

            سوال کاربر: {question}

            لطفاً فقط کوئری SQL خالص تولید کنید بدون هیچ توضیح اضافی. از کامنت استفاده نکنید.
            از فارسی در کوئری استفاده نکنید. فقط از نام‌های ستون‌های انگلیسی استفاده کنید.

            کوئری SQL:
            """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        self.output_parser = SQLOutputParser()

    def generate_sql(self, question: str, table_schema: str) -> str:
        """Generate SQL query from natural language question"""
        response = self.chain.invoke({
            "question": question, 
            "table_schema": table_schema
        })
        return self.output_parser.parse(response["text"])

class ResponseGenerator:
    """Generates final response from SQL results using LLM"""

    def __init__(self):
        self.llm = Ollama(model="llama3.1")
        self.prompt_template = PromptTemplate(
            input_variables=["question", "sql_results", "sql_query"],
            template="""
            شما یک تحلیلگر داده هستید. بر اساس نتایج کوئری SQL و سوال اصلی کاربر، پاسخ جامع و تحلیلی تولید کنید.

            سوال اصلی: {question}

            کوئری SQL اجرا شده:
            {sql_query}

            نتایج کوئری:
            {sql_results}

            لطفاً پاسخ کاملی به فارسی تولید کنید که شامل تحلیل داده‌ها، خلاصه‌ای از یافته‌ها و هر بینش مرتبط باشد.
            پاسخ را به صورت حرفه‌ای و ساختاریافته ارائه دهید.

            پاسخ تحلیلگر:
            """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def generate_response(self, question: str, sql_results: List[Dict], sql_query: str) -> str:
        """Generate final response from SQL results"""
        results_str = json.dumps(sql_results, ensure_ascii=False, indent=2)
        response = self.chain.invoke({
            "question": question,
            "sql_results": results_str,
            "sql_query": sql_query
        })
        return response["text"]

def get_table_schema() -> str:
    """Get the schema of the amayesh table"""
    return """
CREATE TABLE public.amayesh (
	id int4 NULL,
	province text NULL,
	county text NULL,
	"year" int4 NULL,
	"month" text NULL,
	number_of_kindergartens int4 NULL,
	kindergarten_area numeric NULL,
	number_of_kindergartens_with_sports_infrastructure int4 NULL,
	area_of_kindergartens_with_sports_infrastructure numeric NULL,
	number_of_specialized_childrens_play_and_sports_club_centers int4 NULL,
	area_of_specialized_childrens_play_and_sports_club_centers numeric NULL,
	number_of_specialized_childrens_play_and_sports_instructors int4 NULL,
	number_of_playhouses int4 NULL,
	area_of_playhouses numeric NULL,
	number_of_active_instructors_in_playhouses int4 NULL,
	number_of_playgrounds int4 NULL,
	area_of_playgrounds numeric NULL,
	number_of_inactive_playgrounds_with_equipment int4 NULL,
	number_of_active_playgrounds_focused_on_encouraging_more_physic int4 NULL,
	number_of_events_per_month int4 NULL,
	average_number_of_children_participating_per_event int4 NULL,
	area_of_urban_parks_and_open_recreational_spaces numeric NULL,
	number_of_parks_with_sports_equipment int4 NULL,
	total_area_of_dedicated_sports_spaces_in_urban_parks numeric NULL,
	total_number_of_dedicated_mountaineering_environments int4 NULL,
	number_of_specialized_public_cycling_instructors int4 NULL,
	average_number_of_participants_in_events int4 NULL,
	number_of_cycling_events int4 NULL,
	number_of_bicycle_rental_stations int4 NULL,
	length_of_dedicated_bicycle_paths numeric NULL,
	length_of_fitness_trails_and_dedicated_walking_paths numeric NULL,
	number_of_walking_events_held int4 NULL,
	number_of_public_and_fitness_clubs int4 NULL,
	average_number_of_visitors_to_public_and_fitness_clubs_per_mont int4 NULL,
	number_of_active_and_employed_instructors_in_public_clubs int4 NULL,
	total_area_of_licensed_public_and_fitness_clubs numeric NULL,
	number_of_schools_with_dynamic_yards_meeting_ministry_of_educat int4 NULL,
	total_number_of_schools int4 NULL,
	area_of_schools_with_dynamic_yards_meeting_ministry_of_educatio numeric NULL,
	total_area_of_schools numeric NULL,
	number_of_primary_schools_with_sports_infrastructure int4 NULL,
	total_number_of_primary_schools int4 NULL,
	area_of_primary_schools_with_sports_infrastructure numeric NULL,
	total_area_of_primary_schools numeric NULL,
	number_of_secondary_schools_with_sports_infrastructure int4 NULL,
	total_number_of_secondary_schools int4 NULL,
	area_of_secondary_schools_with_sports_infrastructure numeric NULL,
	total_area_of_secondary_schools numeric NULL,
	number_of_public_schools_with_sports_infrastructure int4 NULL,
	total_number_of_public_schools int4 NULL,
	area_of_public_schools_with_sports_infrastructure numeric NULL,
	total_area_of_public_schools numeric NULL,
	number_of_non_profit_schools_with_sports_infrastructure int4 NULL,
	total_number_of_non_profit_schools int4 NULL,
	area_of_non_profit_schools_with_sports_infrastructure numeric NULL,
	total_area_of_non_profit_schools numeric NULL,
	level_of_student_participation_in_sports_activities float4 NULL,
	number_of_insured_organized_athletes int4 NULL,
	number_of_organized_disabled_athletes int4 NULL,
	number_of_sports_instructors_with_international_specialized_gra int4 NULL,
	number_of_sports_instructors_with_specialized_grade_three int4 NULL,
	number_of_sports_instructors_with_specialized_grade_two int4 NULL,
	number_of_sports_instructors_with_specialized_grade_one int4 NULL,
	number_of_sports_instructors_with_other_specialized_grades int4 NULL,
	number_of_sports_referees_with_international_specialized_grade int4 NULL,
	number_of_sports_referees_with_specialized_grade_three int4 NULL,
	number_of_sports_referees_with_specialized_grade_two int4 NULL,
	number_of_sports_referees_with_specialized_grade_one int4 NULL,
	number_of_sports_referees_with_other_specialized_grades int4 NULL,
	number_of_sports_instructors_whose_birthplace_is_the_relevant_c int4 NULL,
	number_of_sports_competitions_held_at_the_national_level int4 NULL,
	number_of_sports_competitions_held_at_the_provincial_level int4 NULL,
	number_of_sports_competitions_held_at_the_international_level int4 NULL,
	total_number_of_sports_competitions_held int4 NULL,
	list_of_sports_disciplines_of_importance_due_to_medal_winning_c text NULL,
	list_of_sports_disciplines_with_capacity_due_to_popularity text NULL,
	list_of_sports_disciplines_with_capacity_due_to_existing_infras text NULL,
	list_of_sports_disciplines_with_capacity_due_to_infrastructure_ text NULL,
	list_of_sports_disciplines_with_capacity_due_to_natural_environ text NULL,
	list_of_sports_disciplines_with_capacity_due_to_physical_and_ge text NULL,
	list_of_sports_disciplines_with_capacity_due_to_neighboring_and text NULL,
	list_of_sports_disciplines_with_capacity_due_to_private_sector_ text NULL,
	list_of_sports_disciplines_with_capacity_due_to_the_reception_b text NULL,
	list_of_popular_and_active_local_traditional_games_at_the_count text NULL,
	in_terms_of_movement_and_skill_which_sports_are_these_games_sim text NULL,
	list_of_strategic_sports_of_the_county_province_from_a_champion text NULL,
	list_of_popular_and_public_sports_of_the_county_province text NULL,
	contact_number_of_the_form_completer text NULL,
	total_number_of_specialized_schools int4 NULL,
	number_of_active_instructors_in_specialized_schools int4 NULL,
	number_of_participants_in_specialized_schools int4 NULL,
	full_name_of_the_form_completer text NULL,
	number_of_sports_referees_whose_birthplace_is_the_relevant_coun int4 NULL,
	number_of_clubs_active_in_various_provincial_and_national_leagu int4 NULL,
	number_of_factories_and_economic_enterprises_supporting_profess int4 NULL,
	number_of_specialized_schools_with_sports_facilities_of_ownersh int4 NULL,
	number_of_specialized_schools_with_sports_facilities_of_rental_ int4 NULL,
	number_of_schools_where_physical_education_class_is_held_in_the int4 NULL,
	area_of_schools_where_physical_education_class_is_held_in_the_s numeric NULL,
	number_of_schools_where_physical_education_class_is_held_in_a_y int4 NULL,
	area_of_schools_where_physical_education_class_is_held_in_a_yar numeric NULL,
	number_of_sports_halls_with_suitable_flooring int4 NULL,
	area_of_sports_halls_with_suitable_flooring numeric NULL,
	report_year int4 NULL,
	number_of_schools_with_sports_infrastructure int4 NULL,
	area_of_schools_with_sports_infrastructure numeric NULL,
	total_medal_winners_of_school_sports_olympiads int4 NULL,
	total_participants_in_school_sports_olympiads int4 NULL,
	total_organized_university_athletes int4 NULL,
	total_participants_whose_birthplace_is_the_relevant_province int4 NULL,
	total_organized_armed_forces_athletes int4 NULL,
	total_sports_instructors int4 NULL,
	total_sports_referees int4 NULL,
	total_athletes_invited_to_the_national_team int4 NULL,
	total_national_team_coaches int4 NULL,
);
    """

class SQLQueryGenerator:
    """Generates SQL queries from natural language using LLM"""
    
    def __init__(self):
        self.llm = Ollama(model="llama3.1")
        self.prompt_template = PromptTemplate(
            input_variables=["question", "table_schema"],
            template="""
            شما یک متخصص SQL هستید. بر اساس سوال کاربر و ساختار جدول، کوئری SQL مناسب تولید کنید.

            ساختار جدول:
            {table_schema}

            سوال کاربر: {question}

            لطفاً فقط کوئری SQL تولید کنید و هیچ توضیح اضافی ندهید.
            از dialect PostgreSQL استفاده کنید.
            """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        self.output_parser = SQLOutputParser()

    def generate_sql(self, question: str, table_schema: str) -> str:
        """Generate SQL query from natural language question"""
        response = self.chain.invoke({
            "question": question, 
            "table_schema": table_schema
        })
        return self.output_parser.parse(response["text"])


# def main():
#     # Initialize components
#     db_connector = DatabaseConnector()
#     sql_generator = SQLQueryGenerator()
#     response_generator = ResponseGenerator()

#     # User question
#     question = "تعداد مهد کودک‌های شهر کرج چنتاست ؟ "
#     # question = "آمار مربیان ورزشی استان تهران و شهرستان تهران به تفکیک سطح تخصص و گرید"

#     print(f"سوال: {question}")
#     print("در حال تولید کوئری SQL...")

#     # Generate SQL query
#     table_schema = get_table_schema()
#     sql_query = sql_generator.generate_sql(question, table_schema)

#     print(f"کوئری تولید شده:\n{sql_query}")
#     print("در حال اجرای کوئری...")

#     # Execute SQL query
#     results = db_connector.execute_query(sql_query)

#     print(f"تعداد نتایج: {len(results)}")

#     if results:
#         print("نتایج کوئری:")
#         for i, row in enumerate(results[:5], 1):  # Show first 5 results
#             print(f"{i}. {row}")

#         # Generate final response
#         print("در حال تولید پاسخ نهایی...")
#         final_response = response_generator.generate_response(question, results, sql_query)

#         print("\n" + "="*50)
#         print("پاسخ نهایی:")
#         print("="*50)
#         print(final_response)
#     else:
#         print("هیچ نتیجه‌ای یافت نشد.")

# if __name__ == "__main__":
#     main()
