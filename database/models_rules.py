from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.session import RulesBase

class HolyQuranGeneralType(RulesBase):
    __tablename__ = 'HolyQuranGeneralType'
    ID = Column(Numeric, primary_key=True)
    Caption = Column(String(50))
    NoAyaat = Column(Numeric)
    IsMaki = Column(Numeric)

class Options(RulesBase):
    __tablename__ = 'Options'
    Item_ID = Column(Integer, primary_key=True)
    Item_Value = Column(Text)
    Item_Text = Column(Text)
    Item_Commen = Column(Text)

class CMBasketItem(RulesBase):
    __tablename__ = 'cmbasketitem'
    ID = Column(Numeric, primary_key=True)
    F_CMBASKETID = Column(Numeric)
    F_SCUSERID = Column(Numeric, nullable=False)
    F_LWLAWID = Column(Numeric, nullable=False)
    F_LWSECTIONID = Column(Numeric)
    F_LWSECTIONLOGID = Column(Numeric)
    ITEMTYPE = Column(Numeric, nullable=False)
    NOTE = Column(String(400))

class CMBasket(RulesBase):
    __tablename__ = 'cmbasket'
    ID = Column(Numeric, primary_key=True)
    F_SCUSERID = Column(Numeric, nullable=False)
    CAPTION = Column(String(100), nullable=False)

class Query(RulesBase):
    __tablename__ = 'Query'
    ID = Column(Integer, primary_key=True)
    QueryTitle = Column(Text)
    QueryText = Column(Text)
    User_ID = Column(Integer)
    Category = Column(Integer)

class LWSectionChange(RulesBase):
    __tablename__ = 'lwsectionchange'
    ID = Column(Numeric, primary_key=True)
    F_LWSECTIONID_EFFECTIVE = Column(Numeric)
    F_LWSECTIONLOGID_EFFECTED = Column(Numeric)
    STATENO = Column(Numeric)
    F_LWLAWID_EFFECTED = Column(Numeric, ForeignKey('lwLaw.ID'))
    OLDID = Column(Numeric)
    EFFECTIVESECTIONFULLPATH = Column(String(400))
    EFFECTEDSECTIONFULLPATH = Column(String(400))
    F_CMBASETABLEID_SECTIONSTATUS = Column(Numeric)
    F_LWLAWID_EFFECTIVE = Column(Numeric)
    F_LWSECTIONID_EFFECTED = Column(Numeric)
    F_LWLAWCHANGEID = Column(Numeric)
    LAWCHANGEDATE = Column(String(10))
    ISIMPLICIT = Column(Numeric)
    DESCRIPTION = Column(Text)
    STATENOCHANGED = Column(Numeric)
    WITHCHILDREN = Column(Numeric)
    ENDDATE = Column(String(10))
    F_LWLAWCHANGEID_CHANGED = Column(Numeric)

class LWUpdate(RulesBase):
    __tablename__ = 'LWUpdate'
    ID = Column(Integer, primary_key=True)
    FromLWlog_ID = Column(Numeric, nullable=False)
    ToLWlog_ID = Column(Numeric, nullable=False)
    Price = Column(Integer, nullable=False)
    AttachedFile_ID = Column(Numeric)
    Comment = Column(Text)
    Title = Column(String(30))
    CreateDate = Column(String(15))

class Section_Type(RulesBase):
    __tablename__ = 'Section_Type'
    ID = Column(Integer)
    Name = Column(String(100))
    KeyWord = Column(String(20))
    Degree = Column(Integer)
    WithParagraphEnd = Column(Integer)
    WithNumber = Column(Integer)
    Order_Number = Column(Integer)
    Format_Style_ID = Column(Integer)
    Section_Type_ID = Column(Integer, primary_key=True)

class Format_Style(RulesBase):
    __tablename__ = 'Format_Style'
    ID = Column(Integer, primary_key=True)
    Style_Name = Column(String(50))
    MainSecion = Column(String(50))
    FontName = Column(String(50))
    FontSize = Column(String(50))
    FontBold = Column(Integer)
    FontColor = Column(String(50))
    Alignment = Column(Integer)
    Icon = Column(String(50))
    Border = Column(Integer)
    Background = Column(String(50))
    FontBackColor = Column(String(50))
    ParagraphSpace = Column(String(50))
    BackImage = Column(String(50))
    Dir = Column(Integer)
    FontItalic = Column(Integer)
    FontUnderline = Column(Integer)

class Terminologi(RulesBase):
    __tablename__ = 'Terminologi'
    ID = Column(Numeric, primary_key=True)
    Word = Column(String(100))
    Detail = Column(Text)

class Dictionary(RulesBase):
    __tablename__ = 'Dictionary'
    English_Farsi_ID = Column(Integer, primary_key=True)
    English_Farsi_Text = Column(Text)
    English_Farsi_Transalates = Column(Text)
    English_Farsi = Column(Integer)

class HolyQuran(RulesBase):
    __tablename__ = 'HolyQuran'
    ID = Column(Numeric, primary_key=True)
    F_HolyQuranGeneralTypeID_NoSoreh = Column(Numeric)
    MatnAyeh = Column(String(2000))
    NoAyeh = Column(Numeric)
    MatnFarsiAyeh = Column(String(2000))
    TranslateFarsi = Column(Text)

class OpOpinionLaw(RulesBase):
    __tablename__ = 'opopinionlaw'
    ID = Column(Numeric, primary_key=True)
    F_OPOPINIONID = Column(Numeric, ForeignKey('opOpinion.ID'))
    F_CMBASETABLEID_OPBASEDOCTYPE = Column(Numeric)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWSECTIONID = Column(Numeric, ForeignKey('lwSection.ID'))
    THECOMMENT = Column(Text)
    HASNOTE = Column(Numeric)
    ISRELATED = Column(Numeric, nullable=False)
    OLDID = Column(Numeric)
    OLDLAWID = Column(Numeric)
    OLDSECTIONID = Column(Numeric)
    F_RULGHANOONID_TMP = Column(Numeric)

class OpOpinionTopic(RulesBase):
    __tablename__ = 'opopiniontopic'
    ID = Column(Numeric, primary_key=True)
    F_OPOPINIONID = Column(Numeric, ForeignKey('opOpinion.ID'))
    F_LWTOPICID = Column(Numeric, ForeignKey('lwTopic.ID'))
    OLDID = Column(Numeric)

class OpOpinion(RulesBase):
    __tablename__ = 'opopinion'
    ID = Column(Numeric, primary_key=True)
    SUBJECT = Column(Text)
    OPINIONLETTERNO = Column(String(60))
    OPINIONDATE = Column(String(10))
    REGISTRATIONNO = Column(String(100))
    ARCHIVENO = Column(String(100))
    F_CMBASETABLEID_CLASSIFICATION = Column(Numeric)
    F_OPOPINIONGIVERID = Column(Numeric)
    F_OPOPINIONGIVERPERSONID = Column(Numeric)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    ISELEMENTARY = Column(Numeric)
    DISTRIBUTENO = Column(String(100))
    DISTRIBUTEDATE = Column(String(10))
    F_PRDOCID = Column(Numeric)
    REALPERSONRECEIVE = Column(Numeric)
    HASNOTE = Column(Numeric)
    THECOMMENT = Column(Text)
    OLDID = Column(Numeric)
    ISBASEINFOCONFIRMED = Column(Numeric)
    ISBASEDOCCONFIRMED = Column(Numeric)
    ISTOPICCONFIRMED = Column(Numeric)
    ISKEYWORDCONFIRMED = Column(Numeric)
    ISHISTORYCONFIRMED = Column(Numeric)
    DOSSIERCLASS = Column(String(400))
    TOTALIMAGE = Column(Numeric)

class CMBaseTableType(RulesBase):
    __tablename__ = 'cmbasetabletype'
    ID = Column(Numeric, primary_key=True)
    CAPTION = Column(String(60), nullable=False)
    SUBSYSTEM = Column(String(20), nullable=False)
    ISREADONLY = Column(Numeric)
    ENGLISHCAPTION = Column(String(60))
    OLDID = Column(Numeric)
    OLDID_MAJLES = Column(Numeric)

class CMBaseTable(RulesBase):
    __tablename__ = 'cmbasetable'
    ID = Column(Numeric, primary_key=True)
    F_CMBASETABLETYPEID = Column(Numeric)
    CAPTION = Column(String(200), nullable=False)
    OLDID = Column(Numeric)
    OLDID_NAZARAT = Column(Numeric)
    ORDERNO = Column(Numeric)

class CMKeyword(RulesBase):
    __tablename__ = 'cmkeyword'
    ID = Column(Numeric, primary_key=True)
    CAPTION = Column(String(600), nullable=False)
    OLDID = Column(Numeric)
    ISFORLAW = Column(Numeric)
    ISFORREGULATION = Column(Numeric)
    ISFORCONGRESS = Column(Numeric)
    ISFOROPINION = Column(Numeric)

class CMOrganization(RulesBase):
    __tablename__ = 'cmorganization'
    ID = Column(Numeric, primary_key=True)
    CAPTION = Column(String(1000), nullable=False)
    F_PARENTID = Column(Numeric)
    F_CMORGANIZATIONID_PREV = Column(Numeric)
    F_CMORGANIZATIONID_NEXT = Column(Numeric)
    FROMDATE = Column(String(10))
    TODATE = Column(String(10))
    F_CMBASETABLEID_ORGTYPE = Column(Numeric)
    THEHIERARCHY = Column(String(400), nullable=False)
    F_RULBASETABLEID = Column(Numeric)
    OLDID = Column(Numeric)
    ISLAWAPPROVER = Column(Numeric)
    ISLAWCOMMANDER = Column(Numeric)
    ISREGULATIONAPPROVER = Column(Numeric)
    ISREGULATIONCOMMANDER = Column(Numeric)
    ISLAWEXECUTOR = Column(Numeric)
    ISLAWRECEIVER = Column(Numeric)
    ISREGULATIONEXECUTOR = Column(Numeric)
    ISREGULATIONRECEIVER = Column(Numeric)
    CODE = Column(String(20))
    ISACTIVE = Column(Numeric)
    HISTORY = Column(String(400))
    ISPLANPROPOSER = Column(Numeric)
    ISPLANSIGNER = Column(Numeric)
    ISPLANOPINIONGIVER = Column(Numeric)

class LWSectionKeyword(RulesBase):
    __tablename__ = 'lwsectionkeyword'
    ID = Column(Numeric, primary_key=True)
    F_LWSECTIONID = Column(Numeric, ForeignKey('lwSection.ID'))
    F_LWSECTIONLOGID = Column(Numeric, ForeignKey('lwSectionLog.ID'))
    F_CMKEYWORDID = Column(Numeric, ForeignKey('cmKeyword.ID'))
    OLDID = Column(Numeric)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))

class LWSectionLog(RulesBase):
    __tablename__ = 'lwsectionlog'
    ID = Column(Numeric, primary_key=True)
    F_LWSECTIONID = Column(Numeric, ForeignKey('lwSection.ID'))
    CAPTION = Column(String(90))
    SECTIONTEXT = Column(Text)
    F_CMBASETABLEID_SECTIONSTATUS = Column(Numeric)
    STATENO = Column(Numeric, nullable=False)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWPHASEID = Column(Numeric, ForeignKey('lwPhase.ID'))
    OLDID = Column(Numeric)
    OLDSTATENO = Column(Numeric)
    F_LWLAWCHANGEID = Column(Numeric, ForeignKey('lwLawChange.ID'))

class LWSectionTopic(RulesBase):
    __tablename__ = 'lwsectiontopic'
    ID = Column(Numeric, primary_key=True)
    F_SECTIONID = Column(Numeric, ForeignKey('lwSection.ID'))
    F_SECTIONLOGID = Column(Numeric, ForeignKey('lwSectionLog.ID'))
    F_TOPICID = Column(Numeric, ForeignKey('lwTopic.ID'))
    OLDID = Column(Numeric)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWPHASEID = Column(Numeric, ForeignKey('lwPhase.ID'))

class LWLawMainNext(RulesBase):
    __tablename__ = 'LWLAWMAINNEXT'
    ID = Column(Numeric, primary_key=True)
    # Additional columns would go here based on full schema

class LWLaw(RulesBase):
    __tablename__ = 'lwLaw'
    ID = Column(Numeric, primary_key=True)
    CAPTION = Column(String(4000))
    F_LWBASETABLEID_LAWTYPE = Column(Numeric)
    F_LWBASETABLEID_CLASSIFICATION = Column(Numeric)
    RULENO = Column(Numeric)
    LAWNO = Column(Numeric)
    APPROVEDATE = Column(String(10))
    F_CMBASETABLEID_LASTSTATUS = Column(Numeric)
    HASEXCEPTION = Column(Numeric)
    ISLAW = Column(Numeric)
    ISREGULATION = Column(Numeric)
    ISCORRECTIONLETTER = Column(Numeric)
    ISOPINION = Column(Numeric)
    OPINIONNO = Column(Numeric)
    CONGRESSNO = Column(Numeric)
    ISCONGRESS = Column(Numeric)
    F_LWBASETABLEID_REGULATIONTYPE = Column(Numeric)
    OLDSHNO = Column(Numeric)
    OLDID = Column(Numeric)
    HASNOTE = Column(Numeric)
    OLDLAWTYPEID = Column(Numeric)
    OLDREGULATIONTYPEID = Column(Numeric)
    OLDLAWNO = Column(Numeric)
    OLDRULENO = Column(Numeric)
    EXPIREDATE = Column(String(10))
    CONTENTTEXT = Column(Text)
    LASTEXPIREDATE = Column(Numeric)
    ISBASEINFOCONFIRMED = Column(Numeric)
    ISSTRUCTURECONFIRMED = Column(Numeric)
    ISTOPICCONFIRMED = Column(Numeric)

class LWLawChange(RulesBase):
    __tablename__ = 'lwLawChange'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    NO = Column(Numeric, nullable=False)
    COMMANDNO = Column(String(52))
    COMMANDDATE = Column(String(10))
    F_CMORGANIZATIONID = Column(Numeric, ForeignKey('cmOrganization.ID'))
    NEWSPAPERNO = Column(String(50))
    NEWSPAPERDATE = Column(String(10))
    LAWTEXT = Column(Text)
    DISTRIBUTETEXT = Column(Text)
    COMMANDTEXT = Column(Text)
    OLDID = Column(Numeric)
    OLDEBLAGHID = Column(Numeric)
    OLDRULGHENTESHARTEXTID = Column(Numeric)
    OLDRULGHEBLAGHTEXTID = Column(Numeric)
    OLDRULGHROZNAMEHID = Column(Numeric)
    APPROVEDATE = Column(String(10))
    HASNOTE = Column(Numeric)
    COMMANPLACE = Column(Numeric)
    COMMANDPLACE = Column(String(80))
    APPROVEDOCDATE = Column(String(10))
    APPROVEDOCNO = Column(String(20))
    DESC1 = Column(String(500))
    DESC2 = Column(String(60))

class LWLawReference(RulesBase):
    __tablename__ = 'lwLawReference'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWSECTIONID = Column(Numeric, ForeignKey('lwSection.ID'))
    F_LWSECTIONLOGID = Column(Numeric, ForeignKey('lwSectionLog.ID'))
    F_LWLAWID_REFERRED = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWSECTIONID_REFERRED = Column(Numeric, ForeignKey('lwSection.ID'))
    DESCRIPTION = Column(Text)
    OLDID = Column(Numeric)
    ISLAWREFERRED = Column(Numeric)

class LWLawRegulation(RulesBase):
    __tablename__ = 'lwLawRegulation'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID_LAW = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWLAWID_REGULATION = Column(Numeric, ForeignKey('lwLaw.ID'))
    NO = Column(Numeric)
    F_LWSECTIONID = Column(Numeric, ForeignKey('lwSection.ID'))
    SECTIONFULLPATH = Column(String(400))
    DESCRIPTION = Column(Text)
    OLDID = Column(Numeric)
    ISREFERENCE = Column(Numeric)
    F_LWSECTIONID2 = Column(Numeric, ForeignKey('lwSection.ID'))

class LWLawsectionStatus(RulesBase):
    __tablename__ = 'lwLawsectionStatus'
    ID = Column(Numeric, primary_key=True)
    CAPTION = Column(String(250), nullable=False)
    USEDFORNEWLAW = Column(Numeric)
    USEDFORLAW = Column(Numeric)
    USEDFORNEWSECTIONLAW = Column(Numeric)
    USEDFORSECTIONLAW = Column(Numeric)
    USEDFORINTERPRETATION = Column(Numeric)
    CHANGETYPE = Column(Numeric)
    OLDID = Column(Numeric)

class LWLawStructure(RulesBase):
    __tablename__ = 'lwLawStructure'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_PARENTID = Column(Numeric, ForeignKey('lwLawStructure.ID'))
    LEVELNO = Column(Numeric, nullable=False)
    F_BASETABLEID_SECTIONTYPE = Column(Numeric)
    OLDID = Column(Numeric)
    NUMBERINGMETHOD = Column(Numeric)
    HIERARCHY = Column(String(600))

class LWReceiver(RulesBase):
    __tablename__ = 'lwReceiver'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_CMORGANIZATIONID = Column(Numeric, ForeignKey('cmOrganization.ID'))
    OLDID = Column(Numeric)

class LWLawFootnote(RulesBase):
    __tablename__ = 'lwLawFootnote'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWSECTIONID = Column(Numeric, ForeignKey('lwSection.ID'))
    F_LWSECTIONLOGID = Column(Numeric, ForeignKey('lwSectionLog.ID'))
    FOOTNOTE = Column(Text)
    LINKEDTEXT = Column(Text)
    OLDID = Column(Numeric)
    ROWNO = Column(Numeric)

class LWApprover(RulesBase):
    __tablename__ = 'lwApprover'
    ID = Column(Numeric, primary_key=True)
    F_LWPHASEID = Column(Numeric, ForeignKey('lwPhase.ID'))
    F_CMORGANIZATIONID = Column(Numeric, ForeignKey('cmOrganization.ID'))
    APPROVEDATE = Column(String(10))
    DESCRIPTION = Column(String(1000))
    OLDID = Column(Numeric)

class LWExecuteCondition(RulesBase):
    __tablename__ = 'lwExecuteCondition'
    ID = Column(Numeric, primary_key=True)
    F_PHASEID = Column(Numeric, ForeignKey('lwPhase.ID'))
    DESCRIPTION = Column(String(4000))
    F_LWSECTIONID_FROM = Column(Numeric, ForeignKey('lwSection.ID'))
    F_LWSECTIONID_TO = Column(Numeric, ForeignKey('lwSection.ID'))
    REGIONNAME = Column(String(1000))
    EXECUTIONDATE = Column(String(10))
    OLDID = Column(Numeric)
    OLDF_RULGHANOONID = Column(Numeric)

class LWLetter(RulesBase):
    __tablename__ = 'lwletter'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LAW_LETTER_ID = Column(Numeric)
    ISTRANSFERIMAGEONLY = Column(Numeric)
    PAGECOUNT = Column(Numeric)

class LWExecutor(RulesBase):
    __tablename__ = 'lwexecutor'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_CMORGANIZATIONID = Column(Numeric, ForeignKey('cmOrganization.ID'))
    OLDID = Column(Numeric)

class LWLawRefer(RulesBase):
    __tablename__ = 'lwlawrefer'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWSECTIONID = Column(Numeric, ForeignKey('lwSection.ID'))
    F_LWLAWID_REFERRED = Column(Numeric, ForeignKey('lwLaw.ID'))
    REFERCOMMENT = Column(String(400))
    LINKEDTEXT = Column(Text)
    SECTIONFULLPATH = Column(String(400))
    OLDID = Column(Numeric)
    F_LWSECTIONID_REFERRED = Column(Numeric, ForeignKey('lwSection.ID'))
    SECTIONREFERREDFULLPATH = Column(Numeric)
    ROWNO = Column(Numeric)
    F_LWSECTIONLOGID = Column(Numeric, ForeignKey('lwSectionLog.ID'))
    ISLAWREFERRED = Column(Numeric)

class PRDoc(RulesBase):
    __tablename__ = 'prdoc'
    ID = Column(Numeric, primary_key=True)
    DOCTEXT = Column(Text)
    OLDID_MAJLES = Column(Numeric)
    OLDID_MAJLES_FINALDEC_FLOWDTL = Column(Numeric)
    OLDID_RULMAJLESMATNID = Column(Numeric)
    OLDID_NAZARAT = Column(Numeric)
    F_RULNAZARID = Column(Numeric)

class OpOpinionGiver(RulesBase):
    __tablename__ = 'opopiniongiver'
    ID = Column(Numeric, primary_key=True)
    F_BASETABLE_OPINIONREF = Column(Numeric)
    CAPTION = Column(String(600))
    F_CMORGANIZATIONID_RESPECTIVE = Column(Numeric, ForeignKey('cmOrganization.ID'))
    F_CMBASETABLEID_OPINIONGROUP = Column(Numeric)
    OLDID = Column(Numeric)

class LWSection(RulesBase):
    __tablename__ = 'lwsection'
    ID = Column(Numeric, primary_key=True)
    CAPTION = Column(String(200))
    F_PARENTID = Column(Numeric, ForeignKey('lwSection.ID'))
    F_CMBASETABLEID_SECTIONSTATUS = Column(Numeric)
    F_LWLAWSTRUCTUREID = Column(Numeric, ForeignKey('lwLawStructure.ID'))
    SECTIONTEXT = Column(Text)
    SECTIONLEVEL = Column(Numeric)
    TEXTORDER = Column(Numeric)
    STATENO = Column(Numeric, nullable=False)
    SECTIONTYPENO = Column(Numeric)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    F_LWPHASEID = Column(Numeric, ForeignKey('lwPhase.ID'))
    OLDID = Column(Numeric)
    FULLPATH = Column(String(600), nullable=False)
    SECTIONTYPENOTEXT = Column(String(100))
    FIRSTSATENO = Column(Numeric)
    LASTSTATENO = Column(Numeric)
    F_LWSECTIONID_REPLACED = Column(Numeric, ForeignKey('lwSection.ID'))
    HIERARCHY = Column(String(500))
    DISPLAYINCONTENTS = Column(Numeric)
    F_LWLAWCHANGEID = Column(Numeric, ForeignKey('lwLawChange.ID'))
    TMP = Column(Numeric)
    F_LWLAWCHANGEID_FIRST = Column(Numeric, ForeignKey('lwLawChange.ID'))
    F_LWLAWCHANGEID_LAST = Column(Numeric, ForeignKey('lwLawChange.ID'))
    ISINTERPRETATION = Column(Numeric)

class LWPhase(RulesBase):
    __tablename__ = 'lwphase'
    ID = Column(Numeric, primary_key=True)
    F_LWLAWID = Column(Numeric, ForeignKey('lwLaw.ID'))
    NO = Column(Numeric, nullable=False)
    COMMANDNO = Column(String(52))
    COMMANDDATE = Column(String(10))
    F_CMORGANIZATIONID = Column(Numeric, ForeignKey('cmOrganization.ID'))
    NEWSPAPERNO = Column(String(50))
    NEWSPAPERDATE = Column(String(10))
    LAWTEXT = Column(Text)
    DISTRIBUTETEXT = Column(Text)
    COMMANDTEXT = Column(Text)
    OLDID = Column(Numeric)
    OLDEBLAGHID = Column(Numeric)
    OLDRULGHENTESHARTEXTID = Column(Numeric)
    OLDRULGHEBLAGHTEXTID = Column(Numeric)
    OLDRULGHROZNAMEHID = Column(Numeric)
    APPROVEDATE = Column(String(10))
    HASNOTE = Column(Numeric)
    COMMANPLACE = Column(Numeric)
    COMMANDPLACE = Column(String(80))
    APPROVEDOCDATE = Column(String(10))
    APPROVEDOCNO = Column(String(20))
    DESC1 = Column(String(500))
    DESC2 = Column(String(60))

class LWTopic(RulesBase):
    __tablename__ = 'lwtopic'
    ID = Column(Numeric, primary_key=True)
    CODE = Column(String(20))
    CAPTION = Column(String(400))
    F_PARENTID = Column(Numeric, ForeignKey('lwTopic.ID'))
    HIERARCHY = Column(String(400))
    OLDID = Column(Numeric)
