from datetime import datetime, date
from otherFunctions import colors
from docx import Document
from docx.text.paragraph import Paragraph
from docx.section import Section
from docx.shared import Pt, Length, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import pymupdf4llm, requests, os, json
from pathlib import Path
from ddgs import DDGS
import time, os, importlib.util, inspect
from types import FunctionType

class ToolDefinitions:
    tool_count : int
    # tool_names : list[str]
    # tool_handles : list[FunctionType] # this will be passed to Ollama

    # ollama should be fed list(tools.values())
    tools : dict[str, FunctionType] # holds function name -> function handle key-value pairs

    def __init__(self):
        self.tool_count = 0
        self.tools = {}
        # self.tool_names = []
        # self.tool_handles = []

        # We will dynamically search for tools in the /src/tools/ directory, specifically, every python file inside of all subfolders in the tools directory.
        # Manually defined functions inside of all located .py files will be considered as tools.
        # Note that Ollama will be passed literal function handles not the string names of functions.
        # Ollama automatically parses the function handle for its docstrings and type hints!

        tools_directory = Path(__file__).resolve().parent / "tools" # locate the path containing all of the folders with the tool python scripts

        # .glob checks one folder deep for the given pattern (any folder with any python file for our case)
        for file in tools_directory.glob("*/*.py"):
            # skip any directories with double underscores in any part of the file path.
            if "__" in file.parts:
                continue

            try:
                # get specification from file
                spec = importlib.util.spec_from_file_location(file.stem, file)

                if spec is None or spec.loader is None: # guard against None values
                    print(f"Skipping {file.name}: Could not load file specification.")
                    return

                # get the module from the spec and load it into memory
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module) # This loads it into memory

                # extract only function handles that were defined inside the python scripts (exclude imports)
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if func.__module__ == file.stem: # exclude imported functions
                        
                        self.tools[name] = func # create new key-value pair using the name and function handle
                        # self.tool_handles.append(func)
                        # self.tool_names.append(name)
                        self.tool_count = self.tool_count + 1
                
            except Exception as e:
                print(f"Failed to import {file.name}: {e}")

            

    # # method to add a single tool by name
    # def add_tool(self, tool_name : str):
    #     """Function to add a single tool to this tool definition object by name. The name should exactly match the tool/function name."""
    #     self.tool_count = self.tool_count + 1
    #     self.tool_names.append(tool_name)

    # def add_tools(self, tool_names : list[str]):
    #     """Function to add a list of tools to this tool definition object by name. The names should exactly match the tool/function names."""
    #     self.tool_count = self.tool_count + len(tool_names)
    #     self.tool_names.extend(tool_names)


# obj = ToolDefinitions().add_tool("get_time")

# # Define a tool that fetches the current time
# def get_time() -> str:
#     """Use this function whenever the current time is requested."""

#     print(colors("get_time() was called!", "blue"))
#     return datetime.now().strftime("%I:%M %p")

# # Define a tool that fetches the current date
# def get_date() -> str:
#     """
#     Use this function whenever the calendar date is requested. The result is in YYYY-MM-DD.
#     """
#     print(colors("get_date() was called!", "blue"))
#     return str(date.today())


# def read_pdf() -> str:
#     """
#     Use this function when info about a resume is requested.
#     """

#     filePath = "C:/Users/ME/Downloads/test/test.pdf"
#     markdown_text = pymupdf4llm.to_markdown(filePath)

#     print(colors("read_pdf() was called!", "blue"))
#     return str(markdown_text)

# def read_word_doc(file_path : str) -> str:
#     """
#     Use this function to read the text and formatting content of word documents. The result is a stringified JSON that holds the text and formatting information.
#     """
#     # file_path = ""
#     doc = Document(file_path) # LATER, ENSURE THE PATH IS RESTRICTED TO PREVENT SECURITY RISKS!!!!
#     document_info = []
#     # doc.paragraphs[0].runs[0].style.
#     from docx.shared import Pt, Length

#     # read all the paragraphs
#     for paragraph in doc.paragraphs:
#         # text_content.join([paragraph.text])

#         style = "Normal"
#         if paragraph.style and paragraph.style.name:
#             style = paragraph.style.name
        
#         font_size = None
#         font_family = None
#         if paragraph.runs:
#             font_size = (paragraph.runs[0].font.size)
#             font_family = paragraph.runs[0].font.name

#         bold = any(run.bold for run in paragraph.runs)
#         italic = any(run.italic for run in paragraph.runs)


#         document_info.append({
#             'text_content': (paragraph.text),
#             'formatting_info': {
#                 'style': style, # this is a string
#                 'font_family': font_family,
#                 'font_size': font_size, # this is cast to a string
#                 'bold': bold, # this is a boolean (or None)
#                 'italic': italic # this is a boolean (or None)
#             }
#         })

#     return json.dumps(document_info, indent=4) # use json.dumps() to get proper json stringification.

# # fully define how the argument should be so the LLM makes less mistakes generating the input argument.
# def create_word_doc(document_info : list[dict[str, str | dict[str, str | bool | None]]]) -> str:
#     """
#     Use this function whenever a new word document must be made.
#     Args:
#         document_info (list): This input argument should be a list of json dictionaries where each dictionary has this exact format:
#             {
#             'text_content': str,
#             'formatting_info': {
#                 'style': str,
#                 'font_family': str,
#                 'font_size': str,
#                 'bold': boolean | None,
#                 'italic': boolean | None
#             }
#             The formatting_info applies to the text_content paired with it and nothing else.
#     Returns:
#         result (str): The path to the newly created document is returned.  
#     """

#     doc = Document()
#     save_file_path = "created-doc.docx"

#     # documents will usually have 1 section, unless a section break was added specifically for a break in the flow of the document formatting
#     # Note that each section is given its own header and footer by default (even if they are blank).

#     # extract the first section from the document to add the resume header
#     main_section = doc.sections[0]
#     header = main_section.header


#     # adjust margins
#     main_section.left_margin = Mm(10)
#     main_section.right_margin = Mm(10)
#     main_section.top_margin = Mm(10)
#     main_section.bottom_margin = Mm(10)

#     # if paragraphs exist already, use the existing paragraphs
#     if header.paragraphs:
#         if len(header.paragraphs)==1:
#             name_header = header.paragraphs[0]
#             name_header.add_run("[Name Here]")
#             info_header = header.add_paragraph("[email] | [phone] | [website]")
#         else:
#             name_header = header.paragraphs[0]
#             name_header.runs[0].text = "[Name Here]"
#             info_header = header.paragraphs[1]
#             info_header.runs[0].text = "[email] | [phone] | [website]"
#     # otherwise, make new paragraphs
#     else:
#         name_header = header.add_paragraph("[Name Here]")
#         info_header = header.add_paragraph("[email] | [phone] | [website]")

#     # Justify the header content
#     name_header.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
#     info_header.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

#     # Apply additional styles
#     name_header.runs[0].bold = True
#     name_header.runs[0].font.size = Pt(20)
#     name_header.runs[0].font.name = "Calibri"
#     info_header.runs[0].font.size = Pt(11)
#     info_header.runs[0].font.name = "Calibri"
#     name_header.paragraph_format.line_spacing = 1.15

    

#     # section = doc.sections[0]
#     # paragraph = section.header.paragraphs[0]
#     # paragraph.text = "Title of document"

#     for info_chunk in document_info:
#         # extract current paragraph text content string and formatting info json
#         text_content = info_chunk.get('text_content')
#         formatting_info = info_chunk.get('formatting_info')

#         assert isinstance(text_content, str)
#         assert isinstance(formatting_info, dict)

#         # fetch the formatting information
#         style = formatting_info.get('style')
#         bold = formatting_info.get('bold')
#         italic = formatting_info.get('italic')
#         font_family = formatting_info.get('font_family')


#         assert isinstance(style, str | None)
#         assert isinstance(font_family, str | None)
#         assert isinstance(bold, bool | None)
#         assert isinstance(italic, bool | None)

#         # create new paragraph in the word document
#         paragraph = doc.add_paragraph()

#         # add a new run to the paragraph (i.e. the literal content)
#         run = paragraph.add_run(text=text_content)
#         run.bold = bold
#         run.italic = italic
#         run.font.name = font_family

#     doc.save(save_file_path)
#     return save_file_path


# def create_resume_from_template(resume_info : dict[str, dict | list | str]) -> str:
#     """
#     Use this function when a resume is being updated, modified or created. A premade resume template is autofilled using the information from the input argument.

#     Args:
#         resume_info (dict): This argument should be a dictionary. Values that are lists have examples of their respective elements. Match the example format exactly excluding the '...'. The argument format is as follows:
#             {
#                 'contact_info': {
#                     'name': str,
#                     'email': str,
#                     'phone': str,
#                     'website': str
#                 },
#                 'profile_summary': str,
#                 'education': [
#                     {
#                         'school': str,
#                         'location': str,
#                         'qualification': str,
#                         'date': str
#                     }, ...
#                 ],
#                 'work_experience': [
#                     {
#                         'job_title': str,
#                         'key_functions': str,
#                         'location': str
#                         'date': str
#                         'bullet_points': [str]
#                     }, ...
#                 ],
#                 'projects': [
#                     {
#                         'project_name': str,
#                         'key_skills': str,
#                         'date': str
#                         'bullet_points': [str]
#                     }, ...
#                 ],
#                 'skills': [
#                     {
#                         'skill_header': str,
#                         'skills': str
#                     }, ...
#                 ],
#                 'certifications': [
#                     {
#                         'name': str,
#                         'date': str
#                     }, ...
#                 ]
#             }

            
#     Returns:
#         result (str): Returns the file path of the newly created resume.

#     """

#     # Define helper function -- applies a bottom border under the given paragraph object. The border acts as a table cell border.
#     def apply_bottom_border(paragraph):
#         """Applies a solid bottom border to a specific paragraph."""
#         pPr = paragraph._p.get_or_add_pPr()
        
#         # Find or create paragraph borders (<w:pBdr>)
#         pBdr = pPr.find(qn('w:pBdr'))
#         if pBdr is None:
#             pBdr = OxmlElement('w:pBdr')
#             pPr.append(pBdr)
        
#         # Remove existing bottom border if it exists to avoid duplicates
#         existing_bottom = pBdr.find(qn('w:bottom'))
#         if existing_bottom is not None:
#             pBdr.remove(existing_bottom)
            
#         # Create and configure the new bottom border element
#         bottom = OxmlElement('w:bottom')
#         bottom.set(qn('w:val'), 'single')     # Border style ('single', 'double', etc.)
#         bottom.set(qn('w:sz'), '10')          # Thickness in eighths of a point (12 = 1.5pt)
#         bottom.set(qn('w:space'), '4')        # Spacing from text
#         bottom.set(qn('w:color'), 'auto')     # Color ('auto' or hex code like 'FF0000')
        
#         pBdr.append(bottom)

#     # creates a right tab stop for the given paragraph (and section).
#     def add_right_tab_stop(section : Section, paragraph : Paragraph):
#         """
#         Places a tab stop at the right side of the document for the given paragraph. This makes it so that a tab stop 
#         (in this paragraph only) places the next content all the way to the right.

#         For example, for a given paragraph, when you add a new run, "Test 1", this text will default to left justified position.
#         Now add another run that starts with a tab; "\tBagels", this text will go all the way to the right side of the screen on the same line as the previous text.

#         The section argument is needed to compute the page width.
        
#         The paragraph argument is the line in which the tab is desired.

#         Note that the paragraph should be defined in the section and not outside of it, otherwise, the tab stop length may have errors.
#         Mismatched placement checks are NOT done.
#         """

#         content_width = section.page_width - section.left_margin - section.right_margin if section.left_margin and section.right_margin and section.page_width else Length(6)
#         paragraph.paragraph_format.tab_stops.add_tab_stop(content_width, WD_TAB_ALIGNMENT.RIGHT)

#     # sets the line spacing to Pt(16) and no space before/after the paragraph
#     def set_paragraph_line_spacing(paragraph : Paragraph):
#         paragraph.paragraph_format.line_spacing = Pt(16)
#         paragraph.paragraph_format.space_before = Pt(0)
#         paragraph.paragraph_format.space_after = Pt(0)


#     # template_path = Path(__file__).resolve().parent / "template-docs" / "resume-template.docx"
#     # doc = Document(str(template_path))
#     doc = Document()
    
#     main_section = doc.sections[0]

#     # adjust margins
#     main_section.left_margin = Mm(10)
#     main_section.right_margin = Mm(10)
#     main_section.top_margin = Mm(10)
#     main_section.bottom_margin = Mm(10)


#     # set normal line spacing and space after paragraphs


#     # extract header information from input argument
#     contact_info = resume_info.get('contact_info')

#     assert isinstance(contact_info, dict)
#     name = contact_info.get('name')
#     email = contact_info.get('email')
#     phone = contact_info.get('phone')
#     website = contact_info.get('website')

#     assert isinstance(name, str)
#     assert isinstance(email, str)
#     assert isinstance(phone, str)
#     assert isinstance(website, str)


#     header = main_section.header

#     # =================================== #
#     #  write and style the resume header  #
#     # =================================== #

#     if header.paragraphs:
#         if len(header.paragraphs) == 1: # apparently new documents default to this case
#             # print("1 paragaph in header already")
#             name_paragraph = header.paragraphs[0]
#             name_paragraph.add_run(name)
#             contact_info_paragraph = header.add_paragraph(email + " | " + phone + " | " + website)
#         else:
#             # print("2 paragraphs in header already...")
#             name_paragraph = header.paragraphs[0]
#             contact_info_paragraph = header.paragraphs[1]

#             name_paragraph.text = name
#             contact_info_paragraph.text = email + " | " + phone + " | " + website
#     else:
#         name_paragraph = header.add_paragraph(name)
#         contact_info_paragraph = header.add_paragraph(email + " | " + phone + " | " + website)


#     name_paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
#     contact_info_paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

#     name_paragraph.runs[0].bold = True
#     name_paragraph.runs[0].font.size = Pt(20)
#     name_paragraph.runs[0].font.name = "Calibri"
#     set_paragraph_line_spacing(name_paragraph)

#     contact_info_paragraph.runs[0].font.size = Pt(11)
#     contact_info_paragraph.runs[0].font.name = "Calibri"
#     apply_bottom_border(contact_info_paragraph)
#     set_paragraph_line_spacing(contact_info_paragraph)


#     # ===================================== #
#     #  write and style the profile summary  #
#     # ===================================== #

#     profile_summary = resume_info.get('profile_summary')
#     assert isinstance(profile_summary, str)
#     if doc.paragraphs:
#         profile_summary_paragraph = doc.paragraphs[0]
#         profile_summary_paragraph.add_run(profile_summary)
#     else:
#         profile_summary_paragraph = doc.add_paragraph(profile_summary)

#     set_paragraph_line_spacing(profile_summary_paragraph)


#     # =============================== #
#     #  write and style the education  #
#     # =============================== #

#     education_info = resume_info.get('education')
#     assert isinstance(education_info, list)

#     education_paragraph = doc.add_paragraph("EDUCATION")
#     apply_bottom_border(education_paragraph)
#     set_paragraph_line_spacing(education_paragraph)

#     for school_info in education_info:
#         school_name = school_info.get('school')
#         location = school_info.get('location')

#         school_paragraph = doc.add_paragraph()
#         add_right_tab_stop(main_section, school_paragraph)
#         set_paragraph_line_spacing(school_paragraph)

#         school_paragraph.add_run(school_name)
#         school_paragraph.add_run("\t" + location)

#         description = school_info.get('description')
#         date = school_info.get('date')

#         description_paragraph = doc.add_paragraph()
#         add_right_tab_stop(main_section, description_paragraph)
#         set_paragraph_line_spacing(description_paragraph)

#         description_paragraph.add_run(description)
#         description_paragraph.add_run("\t" + date)


#     # ===================================== #
#     #  write and style the work experience  #
#     # ===================================== #

#     work_info = resume_info.get('work_experience')
#     assert isinstance(work_info, list)

#     work_paragraph = doc.add_paragraph("WORK EXPERIENCE")
#     apply_bottom_border(work_paragraph)
#     set_paragraph_line_spacing(work_paragraph)

#     for job_info in work_info:
#         job_title = job_info.get('job_title')
#         key_functions = job_info.get('key_functions')
#         location = job_info.get('location')
#         date = job_info.get('date')

#         job_paragraph = doc.add_paragraph()
#         add_right_tab_stop(main_section, job_paragraph)
#         set_paragraph_line_spacing(job_paragraph)

#         job_paragraph.add_run(job_title + " | " + key_functions + " | " + location)
#         job_paragraph.add_run("\t" + date)

#         bullet_points = job_info.get('bullet_points')
#         assert isinstance(bullet_points, list)

#         for point in bullet_points:
#             point_paragraph = doc.add_paragraph(point, style="List Bullet")
#             set_paragraph_line_spacing(point_paragraph)


    
#     # ============================== #
#     #  write and style the projects  #
#     # ============================== #

#     #     {
#     #     'project_name': str,
#     #     'key_skills': str,
#     #     'date': str
#     #     'bullet_points': [str]
#     # }, ...

#     # projects_info = resume_info.get('projects')
#     # assert isinstance(projects_info, list)

#     # projects_paragraph = doc.add_paragraph("PROJECTS")
#     # apply_bottom_border(projects_paragraph)
#     # set_paragraph_line_spacing(projects_paragraph)

#     #  Save the result to /generated-files/
#     path = 'generated-files/new_resume.docx'
#     doc.save(path)

#     return path

# # WEB_SEARCH WORKS BUT READ_URL IS BROKEN!!! -- KEEPS TIMING OUT! ALSO USE A PROXY WHEN PERFORMING WEB SEARCH (NOT IMPLEMENTED YET)! do this later.
# # def read_url(url : str) -> str:
# #     """
# #     Use this function if a url needs to be read or after fetching URLs from a web search. The return value is the raw page html.
# #     """
# #     response = requests.get(url, timeout=5)

# #     print(colors("read_url() was called!", "blue"))

# #     print(response)

# #     return response.text


# # def web_search(query : str, max_results : int = 3) -> str:
# #     """
# #     Use this function to perform web searches if the user requests information unknown to you or if accuracy is very important.
    
# #     Args:
# #         query (str): The literal text content of the web search.
# #         max_results (int): The number of URLs returned by the web search. Default is 3.

# #     Returns:
# #         result (str): A stringified list of json objects with the top URLs and their raw HTML content.

# #     """

# #     try:
# #         with DDGS() as ddgs:
# #             results = []

# #             for r in ddgs.text(query, max_results=max_results):
# #                 url = r.get("href")
# #                 print("URL is : '", url, "'")
# #                 raw_html = read_url(str(url))
# #                 results.append({
# #                     "title": r.get("title"),
# #                     "url": url,
# #                     "raw_html": raw_html
# #                 })
# #                 time.sleep(1003)
# #             print(colors(f"LLM Web search! Query: {query}", "blue"))

# #             return str(results)
        
# #     except Exception as e:
# #         print(colors(f"Web search exception!\n {str(e)}", "red"))
# #         return f"Error Search failed; \n {str(e)}"
# #         # return [{"error": f"Search failed; \n {str(e)}"}]




# # Define a function that the LLM can use to fetch a skill.md file.
# # the skill.md file will tell the LLM (in markdown) in detail what to do to perform a specific action/skill.
# # The LLM is aware of the skills it can use via the system prompt --> put a list of skills that the LLM can use with a line that says:
# # 'Use this skill when the user ___' or some similar use case descriptor
# def get_skill_details(skill_name : str) -> str:
#     """
#     Reads and returns the full instructions for a skill.
#     """
#     print(colors("get_skill_details() was called", "blue"))
#     # basename fetches the literal file stripping away folders/directories. We also remove the .md for now
#     # this prevents directory attacks (reading undersired files)
#     safe_name = os.path.basename(skill_name).replace(".md", "")

#     file_path = f"./skill-files/{safe_name}.md" # assemble path to skill file

#     # read and return file contents if found
#     if os.path.exists(file_path):
#         with open(file_path, "r", encoding="utf-8") as file:
#             contents = file.read()
#             print(contents)
#             return contents
#     return f"Error: Skill '{skill_name}' not found."

