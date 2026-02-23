from docx import Document
import os

def create_docx(filename, text_content):
    doc = Document()
    for line in text_content.split('\n'):
        doc.add_paragraph(line)
    doc.save(filename)
    print(f"Created {filename}")

# Ensure directories exist
os.makedirs("JOB_DESCRIPTIONS", exist_ok=True)
os.makedirs("DATA_resume", exist_ok=True)

# 1. Job Description (Software Engineer)
job_desc = """
Job Title: Senior Software Engineer
Summary:
We are looking for a highly skilled Senior Software Engineer to join our dynamic team. The ideal candidate will have extensive experience in Python, cloud computing, and building scalable applications.

Responsibilities:
- Design and implement scalable backend services using Python and Django/FastAPI.
- Architect and maintain cloud infrastructure on AWS (EC2, S3, Lambda).
- Collaborate with frontend teams to integrate RESTful APIs.
- Write clean, testable, and efficient code.
- Mentor junior developers and conduct code reviews.

Requirements:
- Bachelor's degree in Computer Science or related field.
- 5+ years of experience in software development.
- Strong proficiency in Python and familiarity with Java or C++.
- Experience with containerization technologies like Docker and Kubernetes.
- Solid understanding of database design (PostgreSQL, MongoDB).
- Excellent problem-solving skills and attention to detail.
"""
create_docx("JOB_DESCRIPTIONS/software_engineer_job.docx", job_desc)

# 2. Perfect Match Resume
resume_perfect = """
John Doe
Email: john.doe@example.com | Phone: (555) 123-4567
Summary:
Senior Software Engineer with over 6 years of experience specializing in Python backend development and cloud architecture. Proven track record of delivering scalable solutions on AWS.

Experience:
Senior Backend Developer | Tech Solutions Inc. | 2018 - Present
- Led the migration of legacy monoliths to microservices using Python and FastAPI, improving system reliability by 40%.
- Designed and deployed serverless applications on AWS Lambda and API Gateway.
- Managed containerized deployments using Docker and Kubernetes clusters.
- Optimized PostgreSQL database queries, reducing response times by 50%.

Skills:
- Languages: Python, Java, JavaScript
- Frameworks: Django, FastAPI, Flask, React
- Cloud/DevOps: AWS (EC2, S3, RDS), Docker, Kubernetes, Jenkins
- Databases: PostgreSQL, MongoDB, Redis

Education:
- B.S. in Computer Science | University of Technology | 2014 - 2018
"""
create_docx("DATA_resume/resume_perfect.docx", resume_perfect)

# 3. Partial Match Resume (Data Analyst / Junior Dev)
resume_partial = """
Jane Smith
Email: jane.smith@example.com | Phone: (555) 987-6543
Summary:
Aspiring Software Developer with a background in Data Analysis. Proficient in Python for data scripting and basic web development. Eager to learn cloud technologies.

Experience:
Data Analyst | DataCorp | 2020 - Present
- Automated data reporting workflows using Python scripts (Pandas, NumPy).
- Visualized business metrics using Tableau and Matplotlib.
- Assisted the dev team in basic database maintenance tasks using SQL.

Skills:
- Languages: Python, R, SQL
- Tools: Excel, Tableau, Jupyter Notebooks, Git
- Basic knowledge of: HTML, CSS, Flask

Education:
- B.A. in Statistics | State University | 2016 - 2020
"""
create_docx("DATA_resume/resume_partial.docx", resume_partial)

# 4. No Match Resume (Chef / unrelated)
resume_nomatch = """
Michael Brown
Email: michael.brown@example.com | Phone: (555) 555-5555
Summary:
Experienced Head Chef with a passion for culinary arts and kitchen management. Expert in menu creation, staff training, and inventory control.

Experience:
Head Chef | Gourmet Bistro | 2015 - Present
- Designed seasonal menus featuring locally sourced ingredients.
- Managed a kitchen staff of 15, ensuring high standards of food quality and safety.
- Reduced food waste by 20% through efficient inventory management systems.

Skills:
- Culinary Arts, Menu Planning, Food Safety, Team Leadership
- Inventory Management, Cost Control, Event Catering

Education:
- Culinary Arts Diploma | Culinary Institute | 2013 - 2015
"""
create_docx("DATA_resume/resume_nomatch.docx", resume_nomatch)
