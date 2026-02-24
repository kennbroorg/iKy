"""Tests for backend/factories/iKy_functions.py - pure extraction functions."""

from factories.iKy_functions import (
    extract_hashtags,
    extract_mentions,
    extract_url,
    extract_mails,
    extract_url_linkedin,
    extract_url_instagram,
    extract_url_twitter,
    extract_url_tiktok,
    extract_url_github,
    extract_url_githubio,
    extract_github,
    extract_tiktok,
    extract_twitter,
    extract_instagram,
    extract_linkedin,
    analize_rrss,
    name_match,
    simple_analysis,
    deep_analysis,
)


# -- extract_hashtags --------------------------------------------------------


class TestExtractHashtags:
    def test_single_hashtag(self):
        assert extract_hashtags("hello #world") == ["world"]

    def test_multiple_hashtags(self):
        assert extract_hashtags("#foo #bar #baz") == ["foo", "bar", "baz"]

    def test_no_hashtags(self):
        assert extract_hashtags("no hashtags here") == []

    def test_hashtag_with_underscores(self):
        assert extract_hashtags("#hello_world") == ["hello_world"]

    def test_empty_string(self):
        assert extract_hashtags("") == []


# -- extract_mentions --------------------------------------------------------


class TestExtractMentions:
    def test_single_mention(self):
        result = extract_mentions("hello @user1")
        assert "user1" in result

    def test_multiple_mentions(self):
        # Regex requires a non-word char before @, so "hello @alice and @bob"
        result = extract_mentions("hello @alice and @bob")
        assert "alice" in result
        assert "bob" in result

    def test_no_mentions(self):
        result = [m for m in extract_mentions("no mentions") if m]
        assert result == []

    def test_empty_string(self):
        result = [m for m in extract_mentions("") if m]
        assert result == []


# -- extract_url -------------------------------------------------------------


class TestExtractUrl:
    def test_https_url(self):
        result = extract_url("visit https://example.com today")
        assert len(result) == 1
        assert "example.com" in result[0]["url"]

    def test_http_url(self):
        result = extract_url("visit http://example.com today")
        assert len(result) == 1

    def test_no_urls(self):
        assert extract_url("no urls here") == []

    def test_url_with_path(self):
        result = extract_url("check https://github.com/user/repo out")
        assert len(result) == 1
        assert "github.com/user/repo" in result[0]["url"]


# -- extract_mails -----------------------------------------------------------


class TestExtractMails:
    def test_valid_email(self):
        result = extract_mails("user@example.com")
        assert len(result) == 1
        assert result[0]["email"] == "user@example.com"

    def test_no_email(self):
        assert extract_mails("not an email") == []

    def test_empty_string(self):
        assert extract_mails("") == []


# -- extract_url_linkedin ----------------------------------------------------


class TestExtractUrlLinkedin:
    def test_linkedin_url(self):
        text = "https://www.linkedin.com/in/johndoe/"
        result = extract_url_linkedin(text)
        assert len(result) == 1
        assert result[0]["module"] == "linkedin"
        assert result[0]["param"] == "johndoe"

    def test_no_linkedin(self):
        assert extract_url_linkedin("https://example.com") == []


# -- extract_url_instagram ---------------------------------------------------


class TestExtractUrlInstagram:
    def test_instagram_url(self):
        text = "https://www.instagram.com/johndoe/"
        result = extract_url_instagram(text)
        assert len(result) == 1
        assert result[0]["module"] == "instagram"
        assert result[0]["param"] == "johndoe"

    def test_no_instagram(self):
        assert extract_url_instagram("https://example.com") == []


# -- extract_url_twitter -----------------------------------------------------


class TestExtractUrlTwitter:
    def test_twitter_url(self):
        text = "https://www.twitter.com/johndoe/"
        result = extract_url_twitter(text)
        assert len(result) == 1
        assert result[0]["module"] == "twitter"
        assert result[0]["param"] == "johndoe"

    def test_no_twitter(self):
        assert extract_url_twitter("https://example.com") == []


# -- extract_url_tiktok ------------------------------------------------------


class TestExtractUrlTiktok:
    def test_tiktok_url(self):
        text = "https://www.tiktok.com/@johndoe/"
        result = extract_url_tiktok(text)
        assert len(result) == 1
        assert result[0]["module"] == "tiktok"
        assert result[0]["param"] == "johndoe"

    def test_no_tiktok(self):
        assert extract_url_tiktok("https://example.com") == []


# -- extract_url_github ------------------------------------------------------


class TestExtractUrlGithub:
    def test_github_url(self):
        text = "https://www.github.com/johndoe/"
        result = extract_url_github(text)
        assert len(result) == 1
        assert result[0]["module"] == "github"
        assert result[0]["param"] == "johndoe"

    def test_no_github(self):
        assert extract_url_github("https://example.com") == []


# -- extract_url_githubio ----------------------------------------------------


class TestExtractUrlGithubio:
    def test_githubio_url(self):
        text = "https://johndoe.github.io"
        result = extract_url_githubio(text)
        assert len(result) == 1
        assert result[0]["module"] == "github"
        assert result[0]["param"] == "johndoe"

    def test_no_githubio(self):
        assert extract_url_githubio("https://example.com") == []


# -- extract_github (fuzzy text) ---------------------------------------------


class TestExtractGithub:
    def test_github_mention(self):
        result = extract_github("github: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params

    def test_github_colon_space(self):
        result = extract_github("github: johndoe")
        found_params = [r["param"] for r in result]
        assert "johndoe" in found_params


# -- extract_tiktok (fuzzy text) ---------------------------------------------


class TestExtractTiktok:
    def test_tiktok_mention(self):
        result = extract_tiktok("tiktok: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params


# -- extract_twitter (fuzzy text) --------------------------------------------


class TestExtractTwitter:
    def test_twitter_mention(self):
        result = extract_twitter("twitter: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params


# -- extract_instagram (fuzzy text) ------------------------------------------


class TestExtractInstagram:
    def test_instagram_mention(self):
        result = extract_instagram("instagram: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params


# -- extract_linkedin (fuzzy text) -------------------------------------------


class TestExtractLinkedin:
    def test_linkedin_mention(self):
        result = extract_linkedin("linkedin: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params


# -- analize_rrss ------------------------------------------------------------


class TestAnalizeRrss:
    def test_combines_all_extractors(self):
        text = "#osint @user1 https://www.github.com/testuser/"
        result = analize_rrss(text)
        assert "hashtags" in result
        assert "mentions" in result
        assert "url" in result
        assert "email" in result
        assert "tasks" in result
        assert "osint" in result["hashtags"]

    def test_empty_text(self):
        result = analize_rrss("")
        assert result["hashtags"] == []
        assert result["email"] == []

    def test_with_linkedin_url(self):
        text = "check https://www.linkedin.com/in/johndoe/"
        result = analize_rrss(text)
        task_modules = [t["module"] for t in result["tasks"]]
        assert "linkedin" in task_modules


# -- name_match --------------------------------------------------------------


class TestNameMatch:
    def test_two_names_both_present(self):
        assert name_match(["John", "Doe"], "John Doe is here") is True

    def test_two_names_one_present(self):
        assert name_match(["John", "Doe"], "John is here") is False

    def test_three_names_two_present(self):
        assert name_match(["John", "Michael", "Doe"],
                          "John Doe is here") is True

    def test_three_names_one_present(self):
        assert name_match(["John", "Michael", "Doe"],
                          "John is here") is False

    def test_no_match(self):
        assert name_match(["Alice", "Bob"], "Charlie is here") is False


# -- simple_analysis ---------------------------------------------------------


class TestSimpleAnalysis:
    def test_twitter_url_extraction(self):
        data = [
            "John Doe (@johndoe) | Twitter",
            "https://twitter.com/johndoe",
            "Some description"
        ]
        output = {}
        result = simple_analysis("google", "search", "johndoe", data, output)
        usernames = [u["usernames"] for u in result.get("usernames", [])]
        assert "johndoe" in usernames

    def test_github_url_extraction(self):
        data = [
            "johndoe (John Doe) \u00b7 GitHub",
            "https://github.com/johndoe",
            "Some repos"
        ]
        output = {}
        result = simple_analysis("google", "search", "johndoe", data, output)
        usernames = [u["usernames"] for u in result.get("usernames", [])]
        assert "johndoe" in usernames

    def test_instagram_url_extraction(self):
        data = [
            "John Doe (@johndoe) Instagram profile",
            "https://www.instagram.com/johndoe/",
            "Photos"
        ]
        output = {}
        result = simple_analysis("google", "search", "johndoe", data, output)
        usernames = [u["usernames"] for u in result.get("usernames", [])]
        assert "johndoe" in usernames

    def test_no_social_match(self):
        data = [
            "Random Page",
            "https://example.com/page",
            "Nothing interesting"
        ]
        output = {}
        result = simple_analysis("google", "search", "testuser", data, output)
        assert result.get("usernames", []) == []

    def test_accumulates_output(self):
        """simple_analysis should add to existing output, not replace."""
        existing = {"usernames": [{"source": "prev", "type": "x",
                                   "usernames": "old", "rrss": "test"}]}
        data = [
            "Title",
            "https://twitter.com/newuser",
            "Desc"
        ]
        result = simple_analysis("bing", "search", "newuser", data, existing)
        assert len(result["usernames"]) == 2


# -- deep_analysis -----------------------------------------------------------


class TestDeepAnalysis:
    def test_username_in_url_adds_to_search(self):
        data = [
            "John Doe Profile",
            "https://example.com/johndoe/profile",
            "A description"
        ]
        output = {}
        result = deep_analysis(
            ["John", "Doe"], ["johndoe"], "google", data, output
        )
        assert len(result["search"]) == 1
        assert result["search"][0]["link"] == "google"

    def test_name_in_title_adds_to_search(self):
        data = [
            "John Doe - Developer",
            "https://example.com/some-page",
            "A description"
        ]
        output = {}
        result = deep_analysis(
            ["John", "Doe"], ["otheruser"], "bing", data, output
        )
        assert len(result["search"]) == 1

    def test_no_match_empty_search(self):
        data = [
            "Unrelated Page",
            "https://example.com/page",
            "Nothing about the person"
        ]
        output = {}
        result = deep_analysis(
            ["Alice", "Smith"], ["alicesmith"], "yahoo", data, output
        )
        assert result["search"] == []

    def test_rawresult_always_added(self):
        data = ["Title", "https://url.com", "Desc"]
        output = {}
        result = deep_analysis(["X"], ["y"], "google", data, output)
        assert len(result["rawresult"]) == 1

    def test_searcher_icon_mapping(self):
        data = ["T", "https://u.com/johndoe", "D"]
        for searcher, expected_icon in [
            ("google", "fab fa-google"),
            ("yahoo", "fab fa-yahoo"),
            ("bing", "fab fa-windows"),
            ("duckduckgo", "fas fa-kiwi-bird"),
        ]:
            output = {}
            result = deep_analysis(
                ["John"], ["johndoe"], searcher, data, output
            )
            assert result["rawresult"][0]["icon"] == expected_icon
