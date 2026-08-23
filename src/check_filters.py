"""Minimal self-check for filter rules. Run: python -m src.check_filters"""
from __future__ import annotations

from .filters import dedupe_by_url, inferred_min_years, passes_filters
from .models import Job
from .sources.citi import _parse_results_html

BOARDS = {"relocate_me", "jaabz", "relocate_me_uae", "jaabz_uae"}
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

    uae_board = _pass(
        title="Spring Boot Engineer",
        source="relocate_me_uae",
        region="uae",
        location="Dubai",
        description="no visa word",
    )
    assert uae_board is not None and uae_board.sponsorship is True
    uae_drop = _pass(
        title="Java Developer",
        region="uae",
        source="arbeitnow",
        location="Dubai",
        description="local candidates only",
    )
    assert uae_drop is None

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
    keep_architecture = _pass(
        title="Java Engineer - Software Architecture",
        region="india",
        source="citi",
    )
    assert keep_architecture is not None

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

    from .sources import ey as ey_src

    keep_ey = ey_src._is_india_job(
        _j(
            title="Java Developer",
            source="ey",
            region="india",
            url="https://careers.ey.com/ey/job/Bengaluru-Java-KA-560001/1/",
            location="Bengaluru",
        )
    )
    assert keep_ey is True
    drop_ey_us = ey_src._is_india_job(
        _j(
            title="Java Developer",
            source="ey",
            region="india",
            url="https://careers.ey.com/ey/job/New-York-Java-NY-10001/1/",
            location="New York, United States",
            description="United States",
        )
    )
    assert drop_ey_us is False

    deduped = dedupe_by_url(
        [
            _j(url="https://x.com/a?ref=1"),
            _j(url="https://x.com/a?ref=2"),
            _j(url="https://x.com/b"),
        ]
    )
    assert len(deduped) == 2

    from .scan import carry_over_failed_sources, split_jobs_by_region

    cur = [{"source": "arbeitnow", "url": "https://x.com/a", "region": "eu"}]
    errs = [{"source": "jaabz", "message": "403 Forbidden"}]
    prior = [
        {"source": "jaabz", "url": "https://jaabz.com/jobs/1-java", "region": "eu"},
        {"source": "jaabz", "url": "https://x.com/a", "region": "eu"},  # dup url — skipped
        {"source": "relocate_me", "url": "https://relocate.me/x/y/z/j-1", "region": "eu"},  # not failed
    ]
    kept = carry_over_failed_sources(cur, errs, prior)
    assert kept == 1 and len(cur) == 2
    assert "kept 1 previously saved job" in errs[0]["message"]
    assert carry_over_failed_sources(cur, [], prior) == 0

    split = split_jobs_by_region(
        [
            {"region": "india", "url": "a"},
            {"region": "eu", "url": "b"},
            {"region": "infopark", "url": "c"},
            {"region": "eu", "url": "d"},
            {"region": "uae", "url": "f"},
            {"region": "other", "url": "e"},
        ]
    )
    assert [j["url"] for j in split["india"]] == ["a"]
    assert [j["url"] for j in split["eu"]] == ["b", "d"]
    assert [j["url"] for j in split["infopark"]] == ["c"]
    assert [j["url"] for j in split["uae"]] == ["f"]

    rows, pages = _parse_results_html(
        '<section id="search-results" data-total-pages="3"></section>'
        '<li class="sr-job-item"><h3><a class="sr-job-item__link" '
        'href="/job/pune/java-dev/287/1">Java Dev</a></h3>'
        '<span class="sr-job-location">Pune, India</span></li>'
    )
    assert pages == 3 and rows[0][0] == "Java Dev" and "pune" in rows[0][1]

    from .sources.relocate_me import parse_listing
    from .sources.remotive import is_java_title
    from .sources.jaabz import _cloudflare_block

    rel_jobs: list[Job] = []
    parse_listing(
        """
        <div class="jobs-list__job">
          <a href="/netherlands/amsterdam/picnic/software-engineer-warehouse-systems-10298">
            <div class="job__title">Software Engineer - Warehouse Systems in Amsterdam</div>
            <p class="job__preview">Our Java teams in the Warehouse Systems domain</p>
          </a>
        </div>
        <div class="jobs-list__job">
          <a href="/japan/tokyo/hennge/backend-engineer-1">
            <div class="job__title">Backend Engineer</div>
            <p class="job__preview">Java Spring</p>
          </a>
        </div>
        """,
        rel_jobs,
        set(),
    )
    assert len(rel_jobs) == 1
    assert rel_jobs[0].company == "Picnic"
    assert "Java" in rel_jobs[0].description
    uae_jobs: list[Job] = []
    parse_listing(
        """
        <div class="jobs-list__job">
          <a href="/united-arab-emirates/dubai/talabat/java-engineer-1">
            <div class="job__title">Java Engineer</div>
            <p class="job__preview">Spring Boot</p>
          </a>
        </div>
        <div class="jobs-list__job">
          <a href="/netherlands/amsterdam/picnic/software-engineer-warehouse-systems-10298">
            <div class="job__title">Software Engineer</div>
            <p class="job__preview">Java</p>
          </a>
        </div>
        """,
        uae_jobs,
        set(),
        source_id="relocate_me_uae",
        region="uae",
        country_slug="united-arab-emirates",
    )
    assert len(uae_jobs) == 1
    assert uae_jobs[0].region == "uae" and uae_jobs[0].source == "relocate_me_uae"
    assert is_java_title("Senior Java Engineer")
    assert not is_java_title("Senior Golang Developer")
    from .sources.remotive import add_jobicy_rows, add_remotive_rows

    rem: list[Job] = []
    add_remotive_rows(
        {
            "jobs": [
                {
                    "title": "Java Backend Engineer",
                    "company_name": "Acme",
                    "candidate_required_location": "Europe",
                    "url": "https://remotive.com/remote-jobs/software-dev/java-1",
                    "description": "Spring Boot",
                    "publication_date": "2026-08-01",
                },
                {
                    "title": "Senior Golang Developer",
                    "company_name": "Lemon",
                    "candidate_required_location": "Europe",
                    "url": "https://remotive.com/remote-jobs/software-dev/go-1",
                    "description": "Java, Python, React",
                },
            ]
        },
        rem,
        set(),
    )
    assert len(rem) == 1 and rem[0].company == "Acme"
    icy: list[Job] = []
    add_jobicy_rows(
        {
            "jobs": [
                {
                    "jobTitle": "Java Backend Engineer",
                    "companyName": "BotCo",
                    "jobGeo": "Europe",
                    "url": "https://jobicy.com/jobs/java-eu",
                    "jobDescription": "Spring",
                    "pubDate": "2026-08-01",
                },
                {
                    "jobTitle": "Java Backend Engineer",
                    "companyName": "BotCo",
                    "jobGeo": "APAC",
                    "url": "https://jobicy.com/jobs/java-apac",
                    "jobDescription": "Spring",
                },
            ]
        },
        icy,
        set(),
    )
    assert len(icy) == 1 and "Europe" in icy[0].location
    assert _cloudflare_block("<html>Just a moment... cloudflare challenge-platform</html>")
    assert not _cloudflare_block('<a href="/jobs/266191-senior-java-engineer">Java</a>')

    print("check_filters: ok")


if __name__ == "__main__":
    main()
