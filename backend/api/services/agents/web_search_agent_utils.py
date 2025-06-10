# Esquema del informe
"""
Sections we look at:
• History: Understand its history and most important milestones.
• Business: Understand what it does and its entire value chain (analyze suppliers, customers, competitors, regulators, employees, etc.), possible entry barriers or competitive advantages.
• Market: Who it competes with and what are its market shares (and how they have evolved historically).
• People: Board of directors, management, and shareholders. Who they are, CVs, why they are there, track record, etc. For the management team, how much they earn and what their incentives are based on.
• Capital allocation: Analysis of M&A (amount, multiples, etc.), money allocated to dividends, share buybacks or issuance of shares (at what price they did it).
"""
ESQUEMA = {
    "company_name": "company name",
    "description": "brief description of the company",
    "history": "Most important milestones",
    "business": "Understand what it does, possible entry barriers or competitive advantages. Who are its suppliers and customers.",
    "market": "Who it competes with and what are its market shares",
    "people": "Board of directors, management, and shareholders, who are they? How much does the management team earn and what are their incentives based on",
    "capital_allocation": "Analysis of M&A, money allocated to dividends, share buybacks or issuance",
}
ESQUEMA_MD = """
    ## Company_name
    company name

    ## Description
    brief description of the company

    ## History
    Most important milestones

    ## Business
    Understand what it does, possible entry barriers or competitive advantages. Who are its suppliers and customers.

    ## Market
    Who it competes with and what are its market shares

    ## People
    Board of directors, management, and shareholders - who they are, how much the management team earns and what their incentives are based on

    ## Capital_allocation
    Analysis of M&A, money allocated to dividends, share buybacks or issuance of shares
"""
# Prompt to generate queries about the company to be analyzed. @param: schema, company name, user instructions, maximum number of queries
QUERY_PROMPT = """You are a researcher tasked with creating specific search queries to gather detailed information about a company.

Company you are researching: {company}

Generate 1 search query for each of the following sections of the schema: <sections> {pending_sections} </sections>

<schema> {schema} </schema>

Make simple and clear queries, focusing on finding relevant information about the company.

<user instructions>
{user_notes}
</user instructions>

<instructions> 

1. Generate clear and specific queries for each mentioned section, focusing on obtaining factual and up-to-date information about the company.
2. Ensure that each query focuses on a single aspect to maximize the relevance of the results.
3. Include the company name and relevant business terms in each query.
4. If necessary, break down complex sections into more specific subsections and generate queries for each.
5. Assume the role of a financial analyst when formulating the queries, considering the context and industry of the company.

</instructions>

<Examples of queries>
- For the "people" section:
  - "CEO of {company}"
  - "Board of directors of {company}"

- For the "market" section:
    - "Competitors of {company}"
    - "Market shares of {company}"
    - "Regions of operation of {company}"

- For the "capital_allocation" section:
    - "M&A of {company}"
    - "Dividends of {company}"
    - "Share buybacks of {company}"

</Examples of queries>

Generate the queries following these instructions and examples, ensuring to cover all provided sections with 1 query per section.
Focus on different aspects of the section in order not to do similar queries to the ones already provided:
<queries made>{past_queries}</queries made>
"""

# Prompt to generate notes about the company once the search results are received. @param: schema, company name, user instructions, search results
NOTES_PROMPT = """You are researching the web about the company {company}.

The following schema shows the type of information we are interested in:

<schema> {schema} </schema>
You have just extracted content from a website. Your task is to take clear and organized notes about the company, focusing on topics relevant to our interests.
The extracted content is divided by queries, each query is intended for a section of the schema.
<Website content> {content} </Website content>

Please provide detailed research notes that:

1. Are well-organized and easy to read.
2. Focus on the topics mentioned in the schema.
3. Include specific facts, dates, and figures when available.
4. Maintain the accuracy of the original content.
5. Indicate when important information seems to be missing or unclear with "unknown".
Remember: Do not attempt to format the output to match the schema; just take clear notes that capture all relevant information.
"""

# Prompt to generate notes about the company to be analyzed. @param: schema, company name, user instructions
COMPILER_PROMPT = """
You are a company analysis writer, expert in extracting and organizing relevant data about a company.
Your task is to take the information extracted from web research and apply it to the schema.
The schema may be incomplete, so you should complete it with the extracted information.
Replace or add information.

Stick to changing the following pending sections: {pending_sections}
<schema_to_complete> {schema} </schema_to_complete>

Here is all the research data:

<extracted_info>
{content}
</extracted_info>
Return a markdown text (including markdown features) with the completed text and the extracted information with as much detail as possible.
"""

# Prompt to analyze the extracted information about the company, deciding if it is sufficient or incomplete. @param: schema, company name, extracted content
REFLECTION_PROMPT = """You are a research analyst tasked with reviewing the quality and completeness of the extracted information about a company.

Compare the extracted information with the required schema:

<schema> {schema} </schema>
Here is the extracted information:
<extracted_info>
{content}
</extracted_info>

Analyze if all required fields are present and sufficiently complete, you should be demanding. Consider the following:

1. Is any required field missing specific information?
2. Are there incomplete fields or fields containing uncertain information?
3. Are there fields with placeholder values or indications like "unknown"?"""

import re
def extract_clean_text(markdown_text):
    # Elimina la línea de inicio con "```markdown" y la de cierre con "```"
    text = re.sub(r"^```[a-zA-Z]*\n", "", markdown_text)  # Quita la línea inicial (incluyendo '```markdown')
    text = re.sub(r"\n```$", "", text)  # Quita la línea final con '```'

    # Elimina <schema_to_complete>
    text = re.sub(r"<schema_to_complete>", "", text)
    text = re.sub(r"</schema_to_complete>", "", text)
    return text.strip()


query_prompt_Nsch = """

You are a researcher tasked with creating specific search queries to gather detailed information about the user's query.

Company you are researching: {company}

Make simple and clear queries, focusing on finding relevant information about the user's query.

<user instructions>
{instructions}
</user instructions>

<instructions> 

1. Generate clear and specific queries, focusing on obtaining factual and up-to-date information about the company.
2. Ensure that each query focuses on a single aspect to maximize the relevance of the results.
3. Include the company name and relevant business terms in each query.
4. If necessary, break down complex sections into more specific subsections and generate queries for each.
5. Assume the role of a financial analyst when formulating the queries, considering the context and industry of the company.

</instructions>

Generate the queries following these instructions, ensuring to cover all information needed to answer the question.
Generate 5 queries at max.
Focus on different aspects of the section in order not to do similar queries to the ones already provided:
<queries made>{past_queries}</queries made>
"""

notes_prompt_Nsch = """
You are researching the web about the company {company}.

The following instructions show the type of information we are interested in:

<instruction> {instructions} </instruction>
You have just extracted content from a website. Your task is to take clear and organized notes about the company, focusing on topics relevant to our interests.
<Website content> {content} </Website content>

Please provide detailed research notes that:

1. Are well-organized and easy to read.
2. Focus on the topics mentioned in the schema.
3. Include specific facts, dates, and figures when available.
4. Maintain the accuracy of the original content.
5. Indicate when important information seems to be missing or unclear with "unknown".
"""

compilador_prompt_Nsch="""
You are a company analysis writer, expert in extracting and organizing relevant data about a company.
Your task is to take the information extracted from web research and apply it to the started report or just generate a new one.
The report may be incomplete, so you should complete it with the extracted information.
In case the report isn't started, you should generate a new one.

These are the instructions to follow:
<instruction> {instructions} </instruction>

This is the report to complete:
<report_to_complete> {report} </report_to_complete>

Here is all the research data:

<extracted_info>
{content}
</extracted_info>

Return a markdown text (including markdown features) with the completed report and the extracted information with as much detail as possible.
"""

reflection_prompt_Nsch="""
You are a research analyst tasked with reviewing the quality and completeness of the extracted information about a user query.

These are the instructions received to fulfill the user's request:
<instruction> {instructions} </instruction>


Here is the extracted information currently::
<extracted_info>
{content}
</extracted_info>

Analyze if all critical fields are present and sufficiently complete to complete the user's instructions, you should be demanding. Consider the following:

1. Is any crucial field missing specific information?
2. Are there incomplete fields or fields containing uncertain information?
3. Are there fields with placeholder values or indications like "unknown"?
"""