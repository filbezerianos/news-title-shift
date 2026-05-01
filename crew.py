from crewai import Agent, Crew, LLM, Task


_OLLAMA_LLM = LLM(model="ollama/gemma4:e2b", base_url="http://localhost:11434")


def _format_profile(profile: dict) -> str:
    p = profile
    lines = [
        "=== Reader Profile ===",
        "",
        "Emotional Baseline:",
        f"  - Typical feeling after headlines: {p['emotional_baseline']['q1']}",
        f"  - How long impact lingers: {p['emotional_baseline']['q2']}",
        "",
        "Institutional Trust:",
        f"  - Trust in mainstream outlets: {p['institutional_trust']['q3']}",
        f"  - First instinct when reading a headline: {p['institutional_trust']['q4']}",
        "",
        "Click Motivation:",
        f"  - What makes them click: {p['click_motivation']['q5']}",
        "  - Headline priority ranking (1 = most important):",
        f"      Inform me of facts: {p['click_motivation']['q6_ranking']['inform']}",
        f"      Make me feel something: {p['click_motivation']['q6_ranking']['feel']}",
        f"      Challenge my assumptions: {p['click_motivation']['q6_ranking']['challenge']}",
        f"      Motivate me to act: {p['click_motivation']['q6_ranking']['act']}",
        "",
        "Political & Social Identity:",
        f"  - Political leaning: {p['political_social_identity']['q7']}",
        f"  - Central identities: {', '.join(p['political_social_identity']['q8']) or 'None selected'}",
        "",
        "Perceived Personal Threat:",
        f"  - Current sense of security: {p['perceived_threat']['q9']}",
        f"  - Areas of personal risk: {', '.join(p['perceived_threat']['q10']) or 'None selected'}",
        "",
        "Media Diet:",
        f"  - Primary source of headlines: {p['media_diet']['q11']}",
        f"  - Variety of news sources: {p['media_diet']['q12']}",
        "",
        "Cognitive Style:",
        f"  - How they form opinions: {p['cognitive_style']['q13']}",
        f"  - Reaction to contradicting headlines: {p['cognitive_style']['q14']}",
        "",
        "Current Emotional State:",
        f"  - Right now: {p['current_emotional_state']['q15']}",
        f"  - Mood vs usual: {p['current_emotional_state']['q16']}",
    ]
    return "\n".join(lines)


def run_click_analysis(reader_profile: dict, news_results: list[dict]) -> str:
    """
    reader_profile: st.session_state.reader_profile dict
    news_results: list of {original_title, new_title, publisher, url, date}
    returns: the crew's final analysis as a string
    """

    profile_text = _format_profile(reader_profile)
    headlines_text = "\n".join(
        f"{i + 1}. \"{item['new_title']}\" (original: \"{item['original_title']}\")"
        for i, item in enumerate(news_results)
    )

    persona_agent = Agent(
        role="Reader Persona Analyst",
        goal="Build a clear psychological portrait of a news reader from their profile data.",
        backstory=(
            "You are an expert in media psychology and reader behaviour. "
            "You interpret structured reader profile data to produce a vivid, "
            "accurate description of how a person emotionally and cognitively "
            "engages with news headlines."
        ),
        llm=_OLLAMA_LLM,
        verbose=False,
    )

    click_analyst = Agent(
        role="Headline Click Analyst",
        goal="Predict whether a specific reader persona would click each headline, with a verdict and concise reasoning.",
        backstory=(
            "You are a behavioural analyst specialised in predicting news engagement. "
            "Given a reader persona and a set of headlines, you evaluate click likelihood "
            "based on emotional triggers, trust level, curiosity drivers, and current state."
        ),
        llm=_OLLAMA_LLM,
        verbose=False,
    )

    build_persona_task = Task(
        description=(
            f"Analyse the following reader profile and write a concise psychological "
            f"portrait (4-6 sentences) that captures the key traits influencing how "
            f"this person engages with news headlines.\n\n{profile_text}"
        ),
        expected_output=(
            "A 4-6 sentence portrait covering: emotional reactivity, level of "
            "institutional trust, primary click motivations, and current emotional state."
        ),
        agent=persona_agent,
    )

    analyse_clicks_task = Task(
        description=(
            f"Using the reader persona from the previous task, evaluate each headline below. "
            f"For each one, give:\n"
            f"  - Verdict: Yes / No / Maybe\n"
            f"  - Reason: one sentence explaining why this reader would or would not click\n\n"
            f"Headlines to evaluate:\n{headlines_text}"
        ),
        expected_output=(
            "A numbered list matching the input headlines. Each entry: "
            "verdict (Yes / No / Maybe) followed by a one-sentence reason."
        ),
        agent=click_analyst,
        context=[build_persona_task],
    )

    crew = Crew(
        agents=[persona_agent, click_analyst],
        tasks=[build_persona_task, analyse_clicks_task],
        verbose=False,
    )

    result = crew.kickoff()
    return str(result)
