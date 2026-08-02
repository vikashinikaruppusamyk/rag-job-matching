import os

resume_templates = [
    # Backend Engineers
    {
        "name": "Alice Johnson",
        "years": 7,
        "summary": "Senior Backend Engineer with 7 years building scalable APIs and microservices.",
        "skills": "Python, FastAPI, Django, PostgreSQL, Docker, Kubernetes, AWS, Redis",
        "experience": "Senior Backend Engineer at TechCorp (2021-Present). Built REST APIs serving 50M+ requests/day. Led team of 5 engineers.",
        "education": "B.Tech Computer Science, IIT Delhi (2017)"
    },
    {
        "name": "Bob Smith",
        "years": 4,
        "summary": "Backend Developer with 4 years of experience in building web services.",
        "skills": "Python, Flask, Django, MySQL, Docker, AWS, Git",
        "experience": "Backend Developer at StartupXYZ (2020-Present). Developed microservices using Flask and Docker.",
        "education": "B.S. Computer Science, State University (2020)"
    },
    {
        "name": "Carol Davis",
        "years": 6,
        "summary": "Full Stack Engineer with 6 years in cloud-native development.",
        "skills": "Python, Go, Kubernetes, AWS, PostgreSQL, Docker, Terraform, Redis",
        "experience": "Cloud Engineer at CloudSystems (2019-Present). Architected microservices on Kubernetes.",
        "education": "M.Tech Computer Science, IIIT Bangalore (2018)"
    },
    {
        "name": "David Lee",
        "years": 3,
        "summary": "Junior Backend Engineer with 3 years of Python development.",
        "skills": "Python, Django, PostgreSQL, Docker, GitHub, REST API",
        "experience": "Backend Developer at WebServices Inc (2021-Present). Built APIs using Django REST.",
        "education": "B.Tech IT, VIT University (2021)"
    },
    {
        "name": "Emma Wilson",
        "years": 8,
        "summary": "Principal Engineer with 8 years of experience in distributed systems.",
        "skills": "Python, Java, Go, Kubernetes, AWS, Google Cloud, PostgreSQL, MongoDB, Terraform",
        "experience": "Principal Engineer at BigTech (2018-Present). Led platform team building distributed systems.",
        "education": "B.Tech Computer Science, NIT Trichy (2016)"
    },
    # ML/Data Engineers
    {
        "name": "Frank Chen",
        "years": 5,
        "summary": "Machine Learning Engineer with 5 years in NLP and computer vision.",
        "skills": "Python, TensorFlow, PyTorch, FastAPI, AWS, Docker, PostgreSQL, Machine Learning, Deep Learning",
        "experience": "ML Engineer at AI Systems (2020-Present). Built NLP models in production.",
        "education": "M.S. Computer Science, UC Berkeley (2019)"
    },
    {
        "name": "Grace Martinez",
        "years": 4,
        "summary": "Data Engineer with 4 years of experience in big data systems.",
        "skills": "Python, Spark, Hadoop, PostgreSQL, AWS, Kubernetes, Docker, ETL",
        "experience": "Data Engineer at DataCorp (2021-Present). Built ETL pipelines processing petabytes of data.",
        "education": "B.Tech IT, BITS Pilani (2020)"
    },
    # Full Stack
    {
        "name": "Henry Brown",
        "years": 5,
        "summary": "Full Stack Developer with 5 years of web development experience.",
        "skills": "JavaScript, React, Python, Django, PostgreSQL, Docker, AWS, Node.js, MongoDB",
        "experience": "Full Stack Developer at WebCo (2020-Present). Built customer-facing web applications.",
        "education": "B.S. Software Engineering, Carnegie Mellon (2019)"
    },
    {
        "name": "Iris Patel",
        "years": 6,
        "summary": "Senior Full Stack Engineer with 6 years building end-to-end products.",
        "skills": "JavaScript, TypeScript, React, Python, FastAPI, PostgreSQL, Docker, AWS, GraphQL",
        "experience": "Senior Engineer at StartupABC (2019-Present). Led product development from backend to frontend.",
        "education": "B.Tech IT, NIT Surathkal (2018)"
    },
    # DevOps/Infrastructure
    {
        "name": "Jack Kumar",
        "years": 7,
        "summary": "DevOps Engineer with 7 years of infrastructure and cloud experience.",
        "skills": "Kubernetes, Docker, Terraform, AWS, Google Cloud, CI/CD, Jenkins, Python, Go",
        "experience": "DevOps Lead at CloudInfra (2019-Present). Managed infrastructure for 100+ microservices.",
        "education": "B.Tech Computer Science, JIIT Noida (2017)"
    },
    {
        "name": "Karen White",
        "years": 4,
        "summary": "Infrastructure Engineer with 4 years in cloud platform engineering.",
        "skills": "Kubernetes, Docker, AWS, Terraform, Python, GitHub Actions, Linux",
        "experience": "Infrastructure Engineer at TechStack (2021-Present). Automated deployment pipelines.",
        "education": "B.Tech IT, Manipal University (2021)"
    },
]

def create_resume(name, years, summary, skills, experience, education):
    """Create a formatted resume string."""
    return f"""{name}
Email: {name.lower().replace(' ', '.')}@example.com | Phone: +91-XXXXXXXXXX | LinkedIn: linkedin.com/in/{name.lower().replace(' ', '-')}

PROFESSIONAL SUMMARY
{summary} Experience with cloud technologies, microservices, and modern development practices.

WORK EXPERIENCE
Senior Position at Company (2023-Present)
- Worked on critical systems and architecture decisions
- Led a team of engineers
- Improved system performance by 40%

Mid-Level Position at Organization (2021-2023)
- Developed features using modern technologies
- Mentored junior developers
- {years} years of professional experience

Junior Position at StartupCo (2020-2021)
- Built applications from scratch
- Collaborated with cross-functional teams

EDUCATION
{education}

SKILLS
{skills}

CERTIFICATIONS
AWS Certified Associate (2022)
"""

# Create resumes directory if it doesn't exist
os.makedirs('./data/resumes', exist_ok=True)

# Generate 30 resumes
print("Generating 30 sample resumes...\n")

for i, template in enumerate(resume_templates, 1):
    resume_text = create_resume(
        template['name'],
        template['years'],
        template['summary'],
        template['skills'],
        template['experience'],
        template['education']
    )
    
    filename = f"./data/resumes/resume_{i:02d}_{template['name'].lower().replace(' ', '_')}.txt"
    with open(filename, 'w') as f:
        f.write(resume_text)
    
    print(f"  {i:2d}. {template['name']} ({template['years']} years)")

# If we have less than 30, create variations
if len(resume_templates) < 30:
    print(f"\nCreating {30 - len(resume_templates)} variations...\n")
    
    for i in range(len(resume_templates), 30):
        # Create a variation by modifying an existing template
        base_template = resume_templates[i % len(resume_templates)]
        
        name = f"{base_template['name']} {chr(65 + (i // len(resume_templates)))}"  # Add letter suffix
        years = base_template['years'] + (i % 3)  # Vary years
        
        resume_text = create_resume(
            name, years, base_template['summary'], base_template['skills'],
            base_template['experience'], base_template['education']
        )
        
        filename = f"./data/resumes/resume_{i+1:02d}_{name.lower().replace(' ', '_')}.txt"
        with open(filename, 'w') as f:
            f.write(resume_text)
        
        print(f"  {i+1:2d}. {name} ({years} years)")

print(f"\n✓ Generated 30 resumes in ./data/resumes/")