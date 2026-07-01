"""
modules/assignment_gen.py — Assignment & Study Assistant (Phase 3)
──────────────────────────────────────────────────────────────────
Generates GTU-style assignments, notes, and study materials.

CAPABILITIES:
- Generate Java / OOP / OS / Web Dev / Data Analytics assignments
- Create formatted PDF documents
- Save notes to files
- Summarize topics
- Generate question banks

NOVA COMMANDS THAT TRIGGER THIS:
- "Generate an assignment on Java inheritance"
- "Create notes for Operating System deadlocks"
- "Make a PDF for my Web Development assignment"
- "Give me 10 practice questions for OOP"

SUBJECTS SUPPORTED:
- Java Programming (JP)
- Object-Oriented Programming (OOP)
- Operating Systems (OS)
- Web Development (WD)
- Data Analytics (DA)
- Data Structures (DS)
- Database Management (DBMS)
- Computer Networks (CN)

NOTE: Phase 3 module — included as a fully working implementation
that you can use and extend.
"""

import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class AssignmentGenerator:
    """Generates GTU-style assignments and study materials."""

    def __init__(self, config: dict, ai_brain=None):
        self.config = config
        self.brain = ai_brain  # Use the AI brain to generate content
        self.output_dir = os.path.expanduser("~/Documents/Nova_Assignments")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_assignment(self, subject: str, topic: str, questions: int = 5) -> str:
        """
        Generate a GTU-style assignment.
        
        Args:
            subject: Subject name (e.g., "Java", "Operating Systems")
            topic: Specific topic (e.g., "Inheritance", "Deadlocks")
            questions: Number of questions to generate
        
        Returns:
            Path to the saved markdown file
        """
        if not self.brain:
            return None

        prompt = f"""Generate a GTU (Gujarat Technological University) style assignment for:
Subject: {subject}
Topic: {topic}
Number of questions: {questions}

Format:
1. Create {questions} questions of varying difficulty (basic, intermediate, advanced)
2. Include programming questions if applicable
3. Include marks for each question (total should be around 20-30 marks)
4. Use proper GTU formatting

Make the questions clear, educational, and appropriate for engineering students."""

        content = self.brain.think(prompt)

        # Create the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = topic.replace(" ", "_").lower()
        filename = f"{safe_topic}_assignment_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            f.write(f"# {subject} Assignment\n")
            f.write(f"## Topic: {topic}\n")
            f.write(f"*Generated: {datetime.now().strftime('%B %d, %Y')}*\n\n")
            f.write("---\n\n")
            f.write(content)

        logger.info(f"Assignment saved to: {filepath}")
        return filepath

    def generate_notes(self, subject: str, topic: str) -> str:
        """Generate study notes for a topic."""
        if not self.brain:
            return None

        prompt = f"""Create comprehensive study notes for:
Subject: {subject}
Topic: {topic}

Include:
- Clear explanation of concepts
- Key definitions
- Important points to remember
- Real-world examples
- Common exam questions
- Code examples if it's a programming topic

Format: Well-structured markdown with headers and bullet points."""

        content = self.brain.think(prompt)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = topic.replace(" ", "_").lower()
        filename = f"{safe_topic}_notes_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            f.write(f"# {subject} — {topic}\n")
            f.write(f"*Study Notes — {datetime.now().strftime('%B %d, %Y')}*\n\n")
            f.write("---\n\n")
            f.write(content)

        return filepath

    def open_file(self, filepath: str):
        """Open a generated file in the default app (TextEdit/Preview)."""
        import subprocess
        subprocess.run(["open", filepath], capture_output=True)

    def create_pdf(self, markdown_path: str) -> str:
        """
        Convert a markdown file to PDF.
        Requires: brew install pandoc
        """
        try:
            import subprocess
            pdf_path = markdown_path.replace(".md", ".pdf")
            result = subprocess.run(
                ["pandoc", markdown_path, "-o", pdf_path, "--pdf-engine=xelatex"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return pdf_path
            else:
                logger.warning(f"Pandoc PDF creation failed: {result.stderr}")
                return None
        except FileNotFoundError:
            logger.warning("pandoc not installed. Run: brew install pandoc")
            return None
