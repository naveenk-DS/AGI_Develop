from crewai import Agent, Task, Crew, Process, LLM
from loguru import logger


def get_crew_llm():
    return LLM(
        model="ollama/llama3.1",
        base_url="http://127.0.0.1:11434"
    )


def get_research_crew(topic: str) -> str:
    try:
        llm = get_crew_llm()

        researcher = Agent(
            role="Research Specialist",
            goal=f"Find comprehensive and accurate information about: {topic}",
            backstory=(
                "You are an expert researcher with deep knowledge across "
                "technology, science, business and current events. "
                "You find accurate information quickly and efficiently."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=3
        )

        analyst = Agent(
            role="Data Analyst",
            goal="Analyze research findings and identify key insights",
            backstory=(
                "You are a sharp analyst who spots patterns and extracts "
                "the most important insights from any information."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=2
        )

        summarizer = Agent(
            role="Content Summarizer",
            goal="Create clear concise summaries for voice output",
            backstory=(
                "You are an expert at making complex information simple. "
                "You write in natural conversational language "
                "suitable for being read aloud."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=2
        )

        research_task = Task(
            description=f"Research this topic thoroughly: {topic}. Find key facts, context and relevant details.",
            agent=researcher,
            expected_output="Detailed research findings with key facts"
        )

        analysis_task = Task(
            description="Analyze the research and identify the 3 most important insights.",
            agent=analyst,
            expected_output="3 key insights from the research"
        )

        summary_task = Task(
            description=(
                "Summarize everything in 2-3 natural sentences suitable for speaking aloud. "
                "No bullet points. No markdown. Plain conversational text only."
            ),
            agent=summarizer,
            expected_output="2-3 sentence conversational summary"
        )

        crew = Crew(
            agents=[researcher, analyst, summarizer],
            tasks=[research_task, analysis_task, summary_task],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()
        return str(result).strip()

    except Exception as e:
        logger.error(f"Research crew error: {e}")
        return f"Could not research {topic} right now."


def get_advisory_crew(situation: str) -> str:
    try:
        llm = get_crew_llm()

        advisor = Agent(
            role="Personal Advisor",
            goal=f"Give practical advice for: {situation}",
            backstory=(
                "You are Naveen's trusted personal advisor. "
                "You know he is building NAVIX AI in Chennai. "
                "You give practical, actionable advice tailored to his situation."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=3
        )

        critic = Agent(
            role="Devil's Advocate",
            goal="Challenge the advice and identify potential problems",
            backstory=(
                "You think critically and spot problems others miss. "
                "You help improve decisions by questioning assumptions."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=2
        )

        decider = Agent(
            role="Decision Maker",
            goal="Give the final clear recommendation",
            backstory=(
                "You synthesize all perspectives into one clear actionable recommendation. "
                "You are direct and decisive."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=2
        )

        advice_task = Task(
            description=f"Give practical advice for this situation: {situation}",
            agent=advisor,
            expected_output="Practical advice with reasoning"
        )

        critique_task = Task(
            description="What could go wrong with this advice? What is being overlooked?",
            agent=critic,
            expected_output="Key concerns and counterpoints"
        )

        decision_task = Task(
            description=(
                "Give the final recommendation in 2 sentences maximum. "
                "Be direct. Plain text only, no markdown."
            ),
            agent=decider,
            expected_output="One clear recommendation in 2 sentences"
        )

        crew = Crew(
            agents=[advisor, critic, decider],
            tasks=[advice_task, critique_task, decision_task],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()
        return str(result).strip()

    except Exception as e:
        logger.error(f"Advisory crew error: {e}")
        return f"Could not get advice right now."


def get_code_crew(request: str) -> str:
    try:
        llm = get_crew_llm()

        architect = Agent(
            role="Software Architect",
            goal=f"Design the solution for: {request}",
            backstory=(
                "You are a senior Python developer who designs clean, "
                "efficient solutions. You think about structure before coding."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=3
        )

        coder = Agent(
            role="Python Developer",
            goal="Write clean working Python code",
            backstory=(
                "You write production-quality Python code. "
                "Clean, documented, efficient. No unnecessary complexity."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=3
        )

        reviewer = Agent(
            role="Code Reviewer",
            goal="Review and improve the code",
            backstory=(
                "You review code for bugs, security issues and improvements. "
                "You give specific actionable feedback."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=2
        )

        design_task = Task(
            description=f"Design the solution architecture for: {request}",
            agent=architect,
            expected_output="Solution design and approach"
        )

        code_task = Task(
            description=f"Write Python code for: {request}. Return only the code.",
            agent=coder,
            expected_output="Working Python code"
        )

        review_task = Task(
            description="Review the code and suggest the top 2 improvements.",
            agent=reviewer,
            expected_output="Code review with improvements"
        )

        crew = Crew(
            agents=[architect, coder, reviewer],
            tasks=[design_task, code_task, review_task],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()
        return str(result).strip()

    except Exception as e:
        logger.error(f"Code crew error: {e}")
        return f"Could not write code right now."


def get_planning_crew(goal: str) -> str:
    try:
        llm = get_crew_llm()

        planner = Agent(
            role="Project Planner",
            goal=f"Create a practical plan for: {goal}",
            backstory=(
                "You are an expert project planner who breaks big goals "
                "into clear actionable steps. You are realistic about time and resources."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=3
        )

        prioritizer = Agent(
            role="Priority Specialist",
            goal="Identify the most important first steps",
            backstory=(
                "You know that not all tasks are equal. "
                "You identify the 20% of actions that deliver 80% of results."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
            max_iter=2
        )

        plan_task = Task(
            description=f"Create a step by step plan for: {goal}",
            agent=planner,
            expected_output="Step by step plan"
        )

        priority_task = Task(
            description=(
                "What are the 3 most important first steps? "
                "Format as plain text, no markdown, suitable for speaking aloud."
            ),
            agent=prioritizer,
            expected_output="Top 3 priority steps in plain text"
        )

        crew = Crew(
            agents=[planner, prioritizer],
            tasks=[plan_task, priority_task],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()
        return str(result).strip()

    except Exception as e:
        logger.error(f"Planning crew error: {e}")
        return f"Could not create plan right now."