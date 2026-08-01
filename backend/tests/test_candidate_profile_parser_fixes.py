
from backend.app.services.candidate_profile_parser_service import (
    parse_candidate_profile,
)
SQA_SOURCE = """
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
Rooya Bangladesh
Data Annotation Analyst ? Level Master (LM) Team
Tenure: July 2026 ? Present
[EDUCATION]
B.S.C Information and Communication Engineering (BICE) 2025
Bangladesh University of Professionals (BUP)
CGPA: 3.59 out of 4.00
"""
SHOAIB_SOURCE = """
[CANDIDATE HEADER AND CONTACT]
SHOAIB AHMAD
Phone: 01627026071
Email: shoaib2201@gmail.com
LinkedIn: www.linkedin.com/in/shoaib01627026071
[PROJECTS]
Uncovering Key Themes in Bangladeshi Economic News: A Text Mining and Topic Modeling
Approach
Topic Modeling and Sentiment Analysis of News Articles using R. This project extracts and analyzes
news articles to identify major topics and sentiments, offering insights into economic and investment
related discussions in Bangladeshi media.
Offline, Online, and Back: The Evolution of the UK Grocery Market
In this MIS project, I analyzed the digital transformation and competitive strategies of major UK
grocery retailers, focusing on Tesco and Aldi. The project applied Porter?s Competitive Forces Model to
examine Tesco?s cost leadership strategy, highlighting how economies of scale, supplier negotiations
and technology-driven efficiency sustain its market dominance.
[CERTIFICATIONS]
Data Analytics Career Bootcamp
Institute: Human Development Network Bangladesh
The Data Science Profession ? Student View
Institute: University of London
Python for Data Science, AI & Development
Institute: IBM
Problems, Algorithms and Flowcharts
Statistics and Clustering in Python
2 | P a g e
"""
def test_sqa_work_experience_has_three_records():
    profile = parse_candidate_profile(
        SQA_SOURCE
    )
    assert len(
        profile.work_experience
    ) == 3
    assert (
        profile.work_experience[0]
        .company
        == "IT Division, Trust Bank PLC"
    )
    assert (
        profile.work_experience[2]
        .end_date
        == "Present"
    )
def test_shoaib_has_two_projects_not_description_fragments():
    profile = parse_candidate_profile(
        SHOAIB_SOURCE
    )
    assert len(
        profile.projects
    ) == 2
    assert (
        profile.projects[0]
        .project_title
        == (
            "Uncovering Key Themes in "
            "Bangladeshi Economic News: "
            "A Text Mining and Topic "
            "Modeling Approach"
        )
    )
def test_page_marker_is_not_a_certification():
    profile = parse_candidate_profile(
        SHOAIB_SOURCE
    )
    assert len(
        profile.certifications
    ) == 5
    assert all(
        certification
        .certification_title
        != "2 | P a g e"
        for certification
        in profile.certifications
    )
def test_phone_number_is_removed_from_linkedin_url():
    profile = parse_candidate_profile(
        SHOAIB_SOURCE
    )
    assert (
        profile.contact_information
        .linkedin
        == "www.linkedin.com/in/shoaib"
    )
