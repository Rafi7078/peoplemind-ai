
from backend.app.services.candidate_profile_parser_service import (
    parse_candidate_profile,
)
from backend.app.services.candidate_profile_service import (
    detect_profile_section,
)
ONE_PAGE_SOURCE = """
[CANDIDATE HEADER AND CONTACT]
SALMAN JAHAN RAFI
[WORK EXPERIENCE]
Dec 2024 - Feb 2025
Trust Bank PLC, IT Division (Web Developer)
Intern - In-House Software Development Team
Dream71 Bangladesh Ltd, Development Division Mar 2026 - July 2026
QA Engineer - Software Quality Team
Rooya Bangladesh July 2026 - Present
Data Annotation Analyst - Level Master Team
"""
IP_SOURCE = """
[CANDIDATE HEADER AND CONTACT]
SALMAN JAHAN RAFI
[WORK EXPERIENCE]
Trust Bank PLC, IT Division Dec 2024 - Feb 2025
Intern - In-House Software Development Team
Dream71 Bangladesh Limited, Development Division Jun 2026 - Present
QA Intern - Software Quality Assurance Team
"""
SHOAIB_SOURCE = """
[CANDIDATE HEADER AND CONTACT]
SHOAIB AHMAD
[WORK EXPERIENCE]
Data Annotation Analyst February 2026 - Present
Rooya
Prepared and labeled diverse data types.
"""
def test_experience_heading_variations():
    assert (
        detect_profile_section(
            "Key Professional Experiences"
        )
        == "work_experience"
    )
    assert (
        detect_profile_section(
            "WORK EXPRRIENCE"
        )
        == "work_experience"
    )
def test_one_page_cv_extracts_three_experiences():
    profile = parse_candidate_profile(
        ONE_PAGE_SOURCE
    )
    assert len(
        profile.work_experience
    ) == 3
def test_ip_cv_extracts_two_experiences():
    profile = parse_candidate_profile(
        IP_SOURCE
    )
    assert len(
        profile.work_experience
    ) == 2
def test_shoaib_extracts_title_date_then_company():
    profile = parse_candidate_profile(
        SHOAIB_SOURCE
    )
    assert len(
        profile.work_experience
    ) == 1
    experience = (
        profile.work_experience[0]
    )
    assert (
        experience.company
        == "Rooya"
    )
    assert (
        experience.job_title
        == "Data Annotation Analyst"
    )
