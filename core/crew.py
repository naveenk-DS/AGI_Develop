from crewai import Agent, Task, Crew, Process
from core.llm import get_llm
from loguru import logger

def get_research_crew(topic: str) -> str:
    try:
        llm = get_llm()

        researcher = Agent(
            role="Research Specialist",
            goal=f"Research and find comprehensive information about: {topic}",
            backstory="Expert researcher who finds accurate information quickly.",
            llm=llm,
            verbose=False,
            allow_delegation=False
        )

        summarizer = Agent(
            role="Content Summarizer",
            goal="Summarize research into clear, concise 3-sentence answers",
            backstory="Expert at making complex information simple and clear.",
            llm=llm,
            verbose=False,
            allow_delegation=False
        )

        research_task = Task(
            description=f"Research this topic thoroughly: {topic}",
            agent=researcher,
            expected_output="Detailed research findings"
        )

        summary_task = Task(
            description="Summarize the research in 3 sentences maximum for voice output",
            agent=summarizer,
            expected_output="3 sentence summary suitable for speaking aloud"
        )

        crew = Crew(
            agents=[researcher, summarizer],
            tasks=[research_task, summary_task],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()
        return str(result)
    except Exception as e:
        logger.error(f"Crew error: {e}")
        return f"Could not research {topic}"