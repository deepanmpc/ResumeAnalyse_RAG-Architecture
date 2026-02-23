from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import os

def create_pdf(filename, text_content):
    c = canvas.Canvas(filename, pagesize=LETTER)
    width, height = LETTER
    y_position = height - 50
    
    c.setFont("Helvetica", 12)
    
    # Split text into lines to handle basic wrapping (very simple)
    lines = text_content.split('\n')
    for line in lines:
        if y_position < 50:
            c.showPage()
            y_position = height - 50
            c.setFont("Helvetica", 12)
            
        c.drawString(50, y_position, line)
        y_position -= 15
        
    c.save()
    print(f"Created {filename}")

# Ensure directory exists
os.makedirs("DATA_resume", exist_ok=True)

# 1. Frontend Developer
resume_frontend = """
Alex Rivera
Email: alex.rivera@example.com
Summary:
Creative Frontend Developer with 5 years of experience building responsive web applications. Expert in React and modern JavaScript ecosystem. proven ability to integrate complex backend APIs.

Experience:
Senior Frontend Engineer | WebFlowz Inc. | 2019 - Present
- Built single-page applications using React, Redux, and TypeScript.
- Collaborated closely with backend teams to design and consume RESTful APIs.
- Implemented responsive designs using Tailwind CSS and Material UI.
- Wrote Python scripts to automate asset optimization pipelines.

Skills:
- Frontend: JavaScript (ES6+), TypeScript, React, Vue.js, HTML5, CSS3
- Tools: Webpack, Git, Figma, Jira
- Basic: Python, Node.js, AWS (S3 hosting)

Education:
- B.A. in Graphic Design | Art Institute | 2015 - 2019
"""

# 2. DevOps Engineer
resume_devops = """
Sam Jenkins
Email: sam.jenkins@example.com
Summary:
Cloud Infrastructure Engineer focused on automation, reliability, and security. Extensive experience managing AWS environments and CI/CD pipelines.

Experience:
DevOps Engineer | CloudScale Systems | 2020 - Present
- Architected highly available infrastructure on AWS using Terraform and CloudFormation.
- Managed Kubernetes clusters (EKS) for microservices deployment.
- Developed Python and Bash scripts for system monitoring and auto-scaling.
- Implemented CI/CD pipelines using Jenkins and GitHub Actions.

Skills:
- Cloud: AWS (EC2, VPC, Lambda, RDS, IAM), Google Cloud
- DevOps: Docker, Kubernetes, Terraform, Ansible
- Scripting: Python, Bash, Go
- Monitoring: Prometheus, Grafana, ELK Stack

Education:
- B.S. in Information Systems | State Tech | 2016 - 2020
"""

create_pdf("DATA_resume/resume_frontend_somematch.pdf", resume_frontend)
create_pdf("DATA_resume/resume_devops_somematch.pdf", resume_devops)