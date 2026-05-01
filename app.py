import json
import ollama
import os
import streamlit as st
from gnews import GNews
from crew import run_click_analysis

# Start with the page config
st.set_page_config(
    page_title = "News Titles Shift",
    layout = "wide",
    page_icon = ":material/newspaper:",
    menu_items={
        'About': "News Title Shift v0.1"
    },
    initial_sidebar_state = "collapsed"
)


# The tabs of the main screen
tab_news, tab_config, tab_results = st.tabs([":material/newspaper: News", ":material/settings: Config", ":material/bar_chart: Analysis"])


# Ollama config
schema = {
    "type": "object",
    "properties": {
        "original_title": {"type": "string"},
        "new_title": {"type": "string"},
    },
    "required": ["original_title", "new_title"]
}


# Load saved reader profile on first run
if os.path.exists("reader_profile.json") and os.path.getsize("reader_profile.json") > 0:
    st.write("OK")
    with open("reader_profile.json") as f:
        st.session_state.reader_profile = json.load(f)




# THE NEWS TAB

with tab_news:
    
    st.write("")

    search_query = st.text_input("", placeholder="Search News...", label_visibility="collapsed")

    #st.divider()

    #st.write(search_query)

    if search_query:

        # Only fetch and process if the query has changed since the last run
        if search_query != st.session_state.get("last_search_query"):

            with st.spinner("Getting News...", show_time=True):
                google_news = GNews(max_results=2)
                news = google_news.get_news(search_query)

            st.session_state.news_results = []
            st.session_state.last_search_query = search_query

            for news_item in news:

                with st.spinner("Processing title...", show_time=True):

                    # Process with Ollama

                    message = f"Rewrite the news title {news_item["title"]} to increase the chances of a person to click it. Reply in a json format with the original title and the new title. DO not include anything else in your response."

                    #message = f"Rewrite the news title {news_item["title"]} to make it less possible for the reader to panic and reach emotionally. Reply in a json format with the original title and the new title. DO not include anything else in your response."

                    response = ollama.chat(
                        model="gemma4:e2b",
                        messages=[{'role': 'user', 'content': message}],
                        format=schema
                    )
                    #st.write(response['message']['content'])
                    model_response = json.loads(response['message']['content'])

                st.session_state.news_results.append({
                    "original_title": model_response["original_title"],
                    "new_title":      model_response["new_title"],
                    "publisher":      news_item["publisher"]["title"],
                    "url":            news_item["url"],
                    "date":           news_item["published date"],
                })

        # Display cached results
        for item in st.session_state.get("news_results", []):
            st.divider()
            st.markdown(
                f"<small>:material/newspaper: {item['publisher']} | {item['date']}</small><br>"
                f"<h5 style='margin: 0; padding: 0'><a href='{item['url']}'>{item['new_title']}</a></h5><br>"
                f"<small>{item['original_title']}</small><br>",
                unsafe_allow_html=True
            )

    else:
        #st.info("Search something...")
        pass



# THE READER PROFILE CONFIGURATION TAB

with tab_config:

    st.write("")
    st.markdown("### Reader Profile")
    #st.caption("Configure your profile so news headlines can be adapted to you.")



    # Emotional Baseline questions
    with st.container(border=True):
        emotional_baseline_q1 = st.radio(
            "After reading news headlines, how do you typically feel?",
            ["Calm and informed", "Mildly concerned", "Anxious or unsettled", "Angry or outraged"],
            horizontal=True,
            index=0
        )

    with st.container(border=True):
        emotional_baseline_q2 = st.radio(
            "How long does the emotional impact of a headline usually stay with you?",
            ["It fades immediately", "A few minutes", "Several hours", "It lingers for days"],
            horizontal=True,
            index=0
        )



    # Institutional trust questions
    with st.container(border=True):
        institutional_trust_q1 = st.radio(
            "How much do you trust mainstream news outlets to report accurately?",
            ["Fully, they report facts", "Mostly, with occasional bias", "Little, they have clear agendas", "Not at all, they actively mislead"],
            horizontal=True,
            index=0
        )

    with st.container(border=True):
        institutional_trust_q2 = st.radio(
            "When you read a headline, what is your first instinct?",
            ["Accept it as likely true", "Stay neutral until I read more", "Question who benefits from this story", "Assume it is framed to manipulate me"],
            horizontal=True,
            index=0
        )



    # Click motivation questions
    with st.container(border=True):
        click_motivation_q1 = st.radio(
            "What most often makes you click on a news article?",
            ["It reveals something I didn't know", "It relates to a threat affecting me or my group", "It exposes an injustice or wrongdoing", "It challenges something widely accepted"],
            horizontal=True,
            index=0
        )

    with st.container(border=True):
        click_motivation_q2 = st.multiselect(
            "Rank what a good headline should do from the most important to the least important)",
            ["Inform me of facts", "Make me feel something", "Challenge my assumptions", "Motivate me to act"],
            placeholder="Add in order from the most important to the least important"
        )



    # Political and social identity questions
    with st.container(border=True):
        political_social_identity_q1 = st.radio(
            "How would you describe your political leaning?",
            ["Strongly left / progressive", "Center-left", "Center-right", "Strongly right / conservative"],
            horizontal=True,
            index=0
        )

    with st.container(border=True):
        political_social_identity_q2 = st.multiselect(
            "Put in order what identities feel most central to how you see yourself, from the highest to the lowest?",
            ["My nationality or ethnicity", "My religion or spiritual beliefs", "My economic or class background", "My political values"],
            placeholder="Add in order from the most central to how you see yourself to the least"
        )



    # Perceived personal threat questions
    with st.container(border=True):
        perceived_personal_threat_q1 = st.radio(
            "How safe and secure do you feel in your daily life right now?",
            ["Very secure, things are stable", "Mostly okay, some concerns", "Somewhat vulnerable, things feel uncertain", "Under threat, significantly worried"],
            horizontal=True,
            index=0
        )

    with st.container(border=True):
        perceived_personal_threat_q2 = st.multiselect(
            "In which areas do you feel most at risk personally, from highest to lowest?",
            ["Economic: job, finances, cost of living", "Social: discrimination or exclusion", "Physical: crime or safety", "Political: rights or freedoms being eroded"],
            placeholder="Add in order from the highest risk personally to the lowest"
        )



    # Media diet questions
    with st.container(border=True):
        media_diet_q1 = st.radio(
            "Where do you most often encounter news headlines?",
            ["Social media feeds", "TV or radio", "News websites or apps", "Word of mouth, friends or family"],
            horizontal=True,
            index=0
        )

    with st.container(border=True):
        media_diet_q2 = st.radio(
            "How varied are your news sources?",
            ["I follow many outlets across different perspectives", "I mostly follow 2-3 outlets I trust", "I primarily follow one outlet or platform", "I avoid news outlets and rely on social media"],
            horizontal=True,
            index=0
        )



    # Cognitive style questions
    with st.container(border=True):
        cognitive_style_q1 = st.radio(
            "When you form an opinion, what drives it most?",
            ["Data and evidence I've researched", "Logical reasoning from what I know", "My gut instinct and lived experience", "What people I trust believe"],
            horizontal=True,
            index=0
        )

    with st.container(border=True):
        cognitive_style_q2 = st.radio(
            "When a headline contradicts something you believe, what do you do first?",
            ["Research it immediately", "Feel skeptical and move on", "Feel challenged and want to debate it", "Feel unsettled or defensive"],
            horizontal=True,
            index=0
        )



    # Emotional state questions
    with st.container(border=True):
        emotional_state_q1 = st.radio(
            "How are you feeling right now, in this moment?",
            ["Calm and relaxed", "Focused but neutral", "Mildly stressed or distracted", "Anxious, tense, or upset"],
            horizontal=True,
            index=0
        )

    with st.container(border=True):
        emotion_state_q2_options = ["Better than usual", "About the same", "Slightly worse than usual", "Significantly worse than usual"]
        emotional_state_q2 = st.radio(
            "How would you describe your mood today compared to your usual?",
            ["Better than usual", "About the same", "Slightly worse than usual", "Significantly worse than usual"],
            horizontal=True,
            index=0
        )

    st.write(emotion_state_q2_options.index(emotional_state_q2))


    if st.button("Save Profile", type="primary", icon=":material/save:"):

        with open("reader_profile.json", "w") as f:
            json.dump(st.session_state.reader_profile, f, indent=2)
        st.success("Reader profile saved.")


    ## ── Save to session state ─────────────────────────────────────────────────
    st.session_state.reader_profile = {
        "Emotional baseline questions and answers": {
            "After reading news headlines, how do you typically feel?": emotional_baseline_q1,
            "How long does the emotional impact of a headline usually stay with you?": emotional_baseline_q2
        },
        "Institutional trust questions and answers": {
            "How much do you trust mainstream news outlets to report accurately?": institutional_trust_q1,
            "When you read a headline, what is your first instinct?": institutional_trust_q2
        },
        "Click motivation questions and answers": {
            "What most often makes you click on a news article?": click_motivation_q1,
            "Rank what a good headline should do from the most important to the least important)": click_motivation_q2
        },
        "Political and social identity questions and answers": {
            "How would you describe your political leaning?": political_social_identity_q1,
            "Put in order what identities feel most central to how you see yourself, from the highest to the lowest?": political_social_identity_q2
        },
        "Perceived personal threat questions and answers": {
            "How safe and secure do you feel in your daily life right now?": perceived_personal_threat_q1,
            "In which areas do you feel most at risk personally, from highest to lowest?": perceived_personal_threat_q2
        },
        "Media diet questions and answers": {
            "Where do you most often encounter news headlines?": media_diet_q1,
            "How varied are your news sources?": media_diet_q2
        },
        "Cognitive style questions and answers": {
            "When you form an opinion, what drives it most?": cognitive_style_q1,
            "When a headline contradicts something you believe, what do you do first?": cognitive_style_q2
        },
        "Current emotional state questions and answers": {
            "How are you feeling right now, in this moment?": emotional_state_q1,
            "How would you describe your mood today compared to your usual?": emotional_state_q2
        },
    }


   

with tab_results:

    st.write("")
    st.subheader("Click Analysis")
    st.caption("AI agents evaluate whether you would click each rewritten headline based on your reader profile.")

    news_ready    = bool(st.session_state.get("news_results"))
    profile_ready = bool(st.session_state.get("reader_profile"))

    if not news_ready:
        st.info("Search for news in the News tab first.")
    elif not profile_ready:
        st.info("Configure your reader profile in the Config tab first.")
    else:
        st.markdown("**Headlines queued for analysis:**")
        for item in st.session_state.news_results:
            st.markdown(f"- {item['new_title']}")

        st.write("")

        if st.button("Run Analysis", type="primary"):
            with st.spinner("Agents are analysing your headlines...", show_time=True):
                analysis = run_click_analysis(
                    st.session_state.reader_profile,
                    st.session_state.news_results,
                )
            st.session_state.click_analysis = analysis

        if st.session_state.get("click_analysis"):
            st.divider()
            st.markdown("#### Results")
            st.markdown(st.session_state.click_analysis)


# Debug
st.write(st.session_state.reader_profile)