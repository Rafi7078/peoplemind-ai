
from backend.app.services.candidate_profile_parser_service import (
    parse_candidate_profile,
)
SHOAIB_SOURCE = """
[CANDIDATE HEADER AND CONTACT]
SHOAIB AHMAD
Phone: 01627026071
Email: shoaib2201@gmail.com
LinkedIn: www.linkedin.com/in/shoaib2201
[EDUCATION]
Bachelor of Science in Computer Science and Engineering (CSE)
American International University?Bangladesh (AIUB), Dhaka
CGPA: 3.04 | Year of Completion: 2026
Higher Secondary Certificate (HSC)
Govt. Shah Sultan College, Bogura
GPA: 4.50 | Year of Completion: 2019
[SKILLS]
Programming Languages: Python, R, C++, SQL
Data Science: Data Analysis, Data Visualization, Statistics, Power BI
Web Development: HTML, CSS, JavaScript, PHP, MySQL
[PROJECTS]
Uncovering Key Themes in Bangladeshi Economic News: A Text Mining and Topic Modeling
Approach
Topic Modeling and Sentiment Analysis of News Articles using R.
Offline, Online, and Back: The Evolution of the UK Grocery Market
In this MIS project, I analyzed the digital transformation of UK grocery retailers.
[CERTIFICATIONS]
Data Analytics Career Bootcamp
Institute: Human Development Network Bangladesh
Python for Data Science, AI & Development
Institute: IBM
"""
SALMAN_SOURCE = """
[CANDIDATE HEADER AND CONTACT]
SALMAN JAHAN RAFI
sajidbin7777@gmail.com
01793443264
https://github.com/Rafi7078
[WORK EXPERIENCE]
IT Division, Trust Bank PLC
Intern ? In-House Software Development Team
Tenure: December 2024 ? February 2025
Dream71 Bangladesh Limited
QA Engineer ? Software Development Team
Tenure: March 2026 ? July 2026
[EDUCATION]
B.S.C Information and Communication Engineering (BICE) 2025
Bangladesh University of Professionals (BUP)
CGPA: 3.59 out of 4.00
Higher Secondary Certificate (HSC)
2020
BAF Shaheen College
[SKILLS]
Automation Testing: Playwright, Cypress, Selenium
Programming Languages: Python, JavaScript, SQL
Tools & Platforms: Git, Jira, Power BI
[PROJECTS]
End-to-End Testing with Cypress | Cypress
Implemented end-to-end tests for a web application.
GitHub: https://github.com/example/project
[CERTIFICATIONS]
Deloitte Data Analytics Simulation Program ? Deloitte
Excel Essentials for Workplace Productivity ? UNICEF
"""
def test_parser_extracts_shoaib_profile():
    profile = parse_candidate_profile(
        SHOAIB_SOURCE
    )
    assert profile.candidate_name == "SHOAIB AHMAD"
    assert (
        profile.contact_information.email
        == "shoaib2201@gmail.com"
    )
    assert (
        profile.latest_completed_education
        is not None
    )
    assert (
        profile.latest_completed_education
        .completion_year
        == "2026"
    )
    assert (
        profile.latest_completed_education
        .degree_or_qualification
        == (
            "Bachelor of Science in Computer "
            "Science and Engineering (CSE)"
        )
    )
    assert "Python" in (
        profile.skills.technical_skills
    )
    assert len(profile.projects) == 2
    assert len(profile.certifications) == 2
def test_parser_extracts_salman_profile():
    profile = parse_candidate_profile(
        SALMAN_SOURCE
    )
    assert (
        profile.latest_completed_education
        is not None
    )
    assert (
        profile.latest_completed_education
        .completion_year
        == "2025"
    )
    assert len(
        profile.work_experience
    ) == 2
    assert (
        profile.work_experience[0]
        .start_date
        == "December 2024"
    )
    assert "Cypress" in (
        profile.skills
        .tools_and_platforms
    )
    assert len(profile.projects) == 1
    assert len(profile.certifications) == 2
def test_parser_does_not_return_hsc_when_degree_is_completed():
    profile = parse_candidate_profile(
        SALMAN_SOURCE
    )
    education = (
        profile.latest_completed_education
    )
    assert education is not None
    assert "HSC" not in (
        education.degree_or_qualification
        or ""
    )
