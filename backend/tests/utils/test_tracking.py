import os
import csv
import tempfile
import shutil
from backend.utils.tracking import (
    save_cover_letter_file,
    log_application,
)


class TestSaveCoverLetterFile:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.test_dir)

    def test_save_cover_letter_basic(self):
        """Test basic cover letter saving functionality."""
        job_title = "Software Engineer"
        cover_letter = "This is a test cover letter content."

        save_cover_letter_file(
            job_title, cover_letter, directory=self.test_dir
        )

        # Check that directory was created
        assert os.path.exists(self.test_dir)

        # Check that a file was created
        files = os.listdir(self.test_dir)
        assert len(files) == 1

        # Check filename format
        filename = files[0]
        assert filename.startswith("Software_Engineer_")
        assert filename.endswith(".txt")

        # Check file content
        with open(os.path.join(self.test_dir, filename), "r") as f:
            content = f.read()
            assert content == cover_letter

    def test_save_cover_letter_special_characters(self):
        """Test cover letter saving with special characters in job title."""
        job_title = (
            'Senior Dev/Ops Engineer: "Full Stack" @ Google?'
        )
        cover_letter = "Special characters test content."

        save_cover_letter_file(
            job_title, cover_letter, directory=self.test_dir
        )

        files = os.listdir(self.test_dir)
        assert len(files) == 1

        filename = files[0]
        # Special characters should be replaced with underscores
        assert filename.startswith("Senior_Dev_Ops_Engineer_")
        assert "Full_Stack" in filename
        assert "Google_" in filename
        assert filename.endswith(".txt")

    def test_save_cover_letter_creates_directory(self):
        """Test that save_cover_letter creates the directory if it doesn't exist."""
        nested_dir = os.path.join(self.test_dir, "nested", "path")
        job_title = "Test Job"
        cover_letter = "Test content"

        save_cover_letter_file(
            job_title, cover_letter, directory=nested_dir
        )

        assert os.path.exists(nested_dir)
        files = os.listdir(nested_dir)
        assert len(files) == 1


class TestLogApplication:
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(
            self.temp_dir.name, "applications.csv"
        )

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        self.temp_dir.cleanup()

    def test_log_application_creates_csv(self):
        """Test that log_application creates a CSV file with headers."""
        job_title = "Data Scientist"
        agency = "Tech Corp"
        resume_summary = (
            "Experienced data scientist with ML expertise"
        )

        log_application(
            job_title,
            agency,
            resume_summary,
            filepath=self.test_file,
        )

        assert os.path.exists(self.test_file)

        # Check CSV content
        with open(self.test_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

            assert len(rows) == 2  # Header + 1 data row
            assert rows[0] == [
                "Job Title",
                "Agency",
                "ResumeSummary",
                "DateApplied",
            ]
            assert rows[1][0] == job_title
            assert rows[1][1] == agency
            assert (
                rows[1][2] == resume_summary[:150]
            )  # Should be truncated if longer

    def test_log_application_appends_to_existing(self):
        """Test that log_application appends to existing CSV file."""
        # First application
        log_application(
            "Job 1",
            "Agency 1",
            "Summary 1",
            filepath=self.test_file,
        )

        # Second application
        log_application(
            "Job 2",
            "Agency 2",
            "Summary 2",
            filepath=self.test_file,
        )

        with open(self.test_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

            assert len(rows) == 3  # Header + 2 data rows
            assert rows[0] == [
                "Job Title",
                "Agency",
                "ResumeSummary",
                "DateApplied",
            ]
            assert rows[1][0] == "Job 1"
            assert rows[2][0] == "Job 2"

    def test_log_application_strips_whitespace(self):
        """Test that log_application strips whitespace from inputs."""
        job_title = "  Software Engineer  "
        agency = "  Tech Company  "
        resume_summary = "  ML Engineer with experience  "

        log_application(
            job_title,
            agency,
            resume_summary,
            filepath=self.test_file,
        )

        with open(self.test_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

            assert rows[1][0] == "Software Engineer"  # Stripped
            assert rows[1][1] == "Tech Company"  # Stripped
            assert (
                rows[1][2] == "ML Engineer with experience"
            )  # Stripped

    def test_log_application_truncates_summary(self):
        """Test that resume summary is truncated to 150 characters."""
        long_summary = "A" * 200  # 200 character string
        job_title = "Test Job"
        agency = "Test Agency"

        log_application(
            job_title, agency, long_summary, filepath=self.test_file
        )

        with open(self.test_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

            assert len(rows[1][2]) == 150
            assert rows[1][2] == "A" * 150

    def test_log_application_creates_directory(self):
        """Test that log_application creates the directory if it doesn't exist."""
        nested_file = os.path.join(
            self.temp_dir.name, "subdir", "applications.csv"
        )

        log_application(
            "Job", "Agency", "Summary", filepath=nested_file
        )

        assert os.path.exists(os.path.dirname(nested_file))
        assert os.path.exists(nested_file)

    def test_log_application_timestamp_format(self):
        """Test that the timestamp is in the correct format."""
        import re

        job_title = "Test Job"
        agency = "Test Agency"
        resume_summary = "Test Summary"

        log_application(
            job_title,
            agency,
            resume_summary,
            filepath=self.test_file,
        )

        with open(self.test_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

            timestamp = rows[1][3]
            # Should match YYYYMMDD_HHMMSS format
            assert re.match(r"\d{8}_\d{6}", timestamp)
