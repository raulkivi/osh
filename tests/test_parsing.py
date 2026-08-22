import osh


class TestIsCloudModel:
    def test_colon_cloud_suffix(self):
        assert osh.is_cloud_model("llama3.2:cloud") is True

    def test_dash_cloud_suffix(self):
        assert osh.is_cloud_model("llama3.2-cloud") is True

    def test_non_cloud_model(self):
        assert osh.is_cloud_model("llama3.2") is False


class TestStripCloudSuffix:
    def test_strips_colon_cloud(self):
        assert osh.strip_cloud_suffix("llama3.2:cloud") == "llama3.2"

    def test_strips_dash_cloud(self):
        assert osh.strip_cloud_suffix("llama3.2-cloud") == "llama3.2"

    def test_leaves_non_cloud_names_untouched(self):
        assert osh.strip_cloud_suffix("llama3.2") == "llama3.2"


class TestParseQaVerdicts:
    def test_parses_valid_lines(self):
        response = "1|PASS|Looks safe\n2|FAIL|Deletes data\n3|warn|Irreversible"
        assert osh.parse_qa_verdicts(response) == [
            ("PASS", "Looks safe"),
            ("FAIL", "Deletes data"),
            ("WARN", "Irreversible"),
        ]

    def test_ignores_out_of_range_numbers(self):
        assert osh.parse_qa_verdicts("7|PASS|out of range") == []
        assert osh.parse_qa_verdicts("0|PASS|out of range") == []

    def test_ignores_invalid_verdict_words(self):
        assert osh.parse_qa_verdicts("1|MAYBE|not a real verdict") == []

    def test_ignores_malformed_lines(self):
        assert osh.parse_qa_verdicts("not a verdict line at all") == []

    def test_reason_is_optional(self):
        assert osh.parse_qa_verdicts("1|PASS") == [("PASS", "")]

    def test_blank_input_returns_empty_list(self):
        assert osh.parse_qa_verdicts("") == []


class TestParseCommandOptions:
    def test_parses_tagged_commands_and_explanations(self):
        response = "<c1>ls -la</c1><e1>List all files</e1><c2>pwd</c2><e2>Print directory</e2>"
        assert osh.parse_command_options(response) == [
            ("ls -la", "List all files"),
            ("pwd", "Print directory"),
        ]

    def test_missing_explanation_tag_defaults_to_empty_string(self):
        assert osh.parse_command_options("<c1>ls -la</c1>") == [("ls -la", "")]

    def test_filters_placeholder_commands(self):
        response = "<c1>command here</c1><e1>placeholder</e1>"
        assert osh.parse_command_options(response) == []

    def test_skips_indices_with_no_matching_tag(self):
        response = "<c2>pwd</c2><e2>Print directory</e2>"
        assert osh.parse_command_options(response) == [("pwd", "Print directory")]

    def test_no_tags_returns_empty_list(self):
        assert osh.parse_command_options("no tags here") == []


class TestExtractBaseCommand:
    def test_simple_command(self):
        assert osh.extract_base_command("ls -la") == "ls"

    def test_strips_leading_variable_assignment(self):
        assert osh.extract_base_command("LANG=C ls -la") == "ls"

    def test_stops_at_pipe(self):
        assert osh.extract_base_command("cat file.txt|grep foo") == "cat"

    def test_stops_at_redirect(self):
        assert osh.extract_base_command("echo hi>out.txt") == "echo"

    def test_empty_command_returns_empty_string(self):
        assert osh.extract_base_command("") == ""


class TestSanitizeForLog:
    def test_strips_newlines_and_carriage_returns(self):
        assert osh._sanitize_for_log("line1\nline2\r\nline3") == "line1 line2  line3"

    def test_plain_string_is_unchanged(self):
        assert osh._sanitize_for_log("plain text") == "plain text"
