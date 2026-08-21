"""Minimal self-check for filter rules. Run: python -m src.check_filters"""
from __future__ import annotations

from .filters import dedupe_by_url, inferred_min_years, passes_filters
from .models import Job

BOARDS = {"relocate_me", "jaabz"}
EDU = ["master's", "masters", "m.tech", "mtech", "mba", "m.s", "postgraduate"]


def _j(**kwargs) -> Job:
    base = dict(
        title="Software Engineer",
        company="Acme",
        location="Amsterdam",
        url="https://example.com/1",
        source="arbeitnow",
        region="eu",
        sponsorship=False,
        description="",
    )
    base.update(kwargs)
    return Job(**base)


def _pass(**kwargs):
    return passes_filters(
        _j(**kwargs),
        keywords=["java", "spring boot"],
        exclude_levels=["intern", "graduate", "campus", "trainee", "apprentice"],
        sponsorship_keywords=["visa", "sponsorship", "relocation"],
        sponsorship_board_ids=BOARDS,
        max_years=4,
        exclude_education=EDU,
        exclude_seniority=[
            "assistant vice president",
            "vice president",
            "principal engineer",
            "staff engineer",
            "architect",
            "director",
        ],
    )


def main() -> None:
    keep = _pass(title="Java Backend Engineer", description="visa sponsorship available")
    assert keep is not None and keep.sponsorship is True

    drop_level = _pass(title="Java Intern", description="visa sponsorship")
    assert drop_level is None

    drop_no_sponsor = _pass(title="Java Developer", description="local candidates only")
    assert drop_no_sponsor is None

    board = _pass(title="Spring Boot Engineer", source="relocate_me", description="no visa word")
    assert board is not None

    india = _pass(
        title="Java Engineer",
        region="india",
        source="jpmorgan",
        location="Bengaluru",
    )
    assert india is not None and india.sponsorship is False

    # Experience fit (3.5y profile, max_years=4)
    assert inferred_min_years("3-5 years Java") == 3
    assert inferred_min_years("8+ years of experience") == 8
    keep_range = _pass(title="Java Developer", description="3-5 years experience, visa sponsorship")
    assert keep_range is not None
    drop_senior = _pass(title="Java Developer", description="8+ years experience, visa sponsorship")
    assert drop_senior is None
    drop_five_plus = _pass(title="Java Engineer (5+)", description="visa sponsorship")
    assert drop_five_plus is None

    # Lead titles are allowed (not in exclude_seniority); AVP/architect still blocked for India/EU
    keep_lead = _pass(
        title="Lead Software Engineer - Java AWS Kafka",
        region="india",
        source="jpmorgan",
    )
    assert keep_lead is not None
    drop_avp = _pass(
        title="Technical Lead (Core Java) - Assistant Vice President",
        region="india",
        source="citi",
    )
    assert drop_avp is None
    keep_se3 = _pass(
        title="Software Engineer III - Java",
        region="india",
        source="jpmorgan",
    )
    assert keep_se3 is not None

    # Infopark: no Java/Spring or seniority required
    keep_infopark = _pass(
        title="Senior Software Engineer",
        region="infopark",
        source="infopark",
        description="Senior Software Engineer",
    )
    assert keep_infopark is not None
    keep_infopark_arch = _pass(
        title="AWS Cloud Architect",
        region="infopark",
        source="infopark",
    )
    assert keep_infopark_arch is not None
    # India still drops architect
    drop_india_arch = _pass(
        title="AWS Cloud Architect Java",
        region="india",
        source="citi",
    )
    assert drop_india_arch is None

    # Masters requirement
    drop_masters = _pass(
        title="Java Developer",
        description="Master's degree required. Visa sponsorship available.",
    )
    assert drop_masters is None
    keep_btech = _pass(
        title="Java Developer",
        description="B.Tech / Bachelor's preferred. Visa sponsorship.",
    )
    assert keep_btech is not None

    deduped = dedupe_by_url(
        [
            _j(url="https://x.com/a?ref=1"),
            _j(url="https://x.com/a?ref=2"),
            _j(url="https://x.com/b"),
        ]
    )
    assert len(deduped) == 2

    print("check_filters: ok")


if __name__ == "__main__":
    main()
