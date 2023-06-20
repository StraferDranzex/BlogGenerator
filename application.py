import requests
import urllib3
import time
import streamlit as st
import nltk
import openai

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def generate_blog_articles(keywords, topics, tone, openai_api_key):
    blog_articles = []

    for keyword in keywords:
        for topic in topics:
            title = generate_title(keyword, topic, openai_api_key)

            prompt = f"Write a {tone} blog article with the title: {title}\n\n"

            # Generate the article using Langchain or GPT model
            openai.api_key = openai_api_key
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=1000,
                n=1,
                stop=None,
                temperature=0.7,
            )
            article = response.choices[0].text.strip()

            # Append the generated article to the list
            blog_articles.append(
                {
                    "title": title,
                    "article": article,
                }
            )

            # Introduce a delay between each API call
            time.sleep(5)

    return blog_articles


def publish_articles_on_wordpress(
    blog_articles, category_name, wordpress_domain, admin_username, admin_password
):
    # Authenticate with WordPress using admin username and password
    login_url = f"https://{wordpress_domain}/wp-json/jwt-auth/v1/token"
    login_data = {"username": admin_username, "password": admin_password}
    login_response = requests.post(login_url, params=login_data, verify=False)
    if login_response.status_code != 200:
        st.error(
            "Failed to authenticate with WordPress. Please check your admin username and password."
        )
        return
    else:
        st.success("Login was successful, about to post the articles!")

    token = login_response.json().get("token")

    # Get the category ID based on the selected category name
    category_id = get_category_id(category_name, wordpress_domain)

    if category_id is None:
        st.error(f"Failed to find category ID for category: {category_name}")
        return

    # Publish blog articles on WordPress website
    url = f"https://{wordpress_domain}/wp-json/wp/v2/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for i, article_info in enumerate(blog_articles, start=1):
        title = article_info["title"]
        article = article_info["article"]

        data = {
            "title": title,
            "content": article,
            "status": "publish",
            "categories": [category_id],  # Pass category ID as a list
        }

        response = requests.post(url, json=data, headers=headers, verify=False)
        if response.status_code == 201:
            st.success(f"Article {i} published successfully!")
        else:
            st.error(f"Failed to publish Article {i}. Error: {response.text}")


def generate_title(keyword, topic, openai_api_key):
    prompt = f"Generate a title for a blog article about {keyword.strip()} and {topic.strip()}. Keep the title within 50 tokens."

    # Generate the title using the GPT model
    openai.api_key = openai_api_key
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.7,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    title = response.choices[0].text.strip().replace('"', "")

    return title


def get_categories(wordpress_domain):
    categories_url = f"https://{wordpress_domain}/wp-json/wp/v2/categories?per_page=100"
    response = requests.get(categories_url)
    categories = response.json()
    return categories


def get_category_id(category_name, wordpress_domain):
    categories_url = f"https://{wordpress_domain}/wp-json/wp/v2/categories?per_page=100"
    response = requests.get(categories_url)
    categories = response.json()

    for category in categories:
        if category["name"] == category_name:
            return category["id"]

    return None


def main():
    st.title("Blog Post Generator")

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

    st.subheader("Enter Your Input")

    keywords = st.text_input(
        "Keywords (separated by comma)", value=st.session_state.get("keywords", "")
    )
    st.session_state.keywords = keywords

    topics = st.text_input(
        "Topics (separated by comma)", value=st.session_state.get("topics", "")
    )
    st.session_state.topics = topics

    tone_options = ["Funny", "Serious", "Informative"]
    tone = st.selectbox(
        "Tone",
        tone_options,
        index=tone_options.index(st.session_state.get("tone", ""))
        if st.session_state.get("tone", "") in tone_options
        else 0,
    )
    st.session_state.tone = tone

    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.get("openai_api_key", ""),
    )
    st.session_state.openai_api_key = openai_api_key

    wordpress_domain = st.text_input(
        "WordPress Domain", value=st.session_state.get("wordpress_domain", "")
    )
    st.session_state.wordpress_domain = wordpress_domain

    admin_username = st.text_input(
        "WordPress Admin Username", value=st.session_state.get("admin_username", "")
    )
    st.session_state.admin_username = admin_username

    admin_password = st.text_input(
        "WordPress Admin Password",
        type="password",
        value=st.session_state.get("admin_password", ""),
    )
    st.session_state.admin_password = admin_password

    if wordpress_domain:
        categories = get_categories(wordpress_domain)
        category_names = [category["name"] for category in categories]
        if category_names:
            category_name = st.selectbox(
                "Category",
                category_names,
                index=category_names.index(st.session_state.get("category_name", ""))
                if st.session_state.get("category_name", "") in category_names
                else 0,
            )
            st.session_state.category_name = category_name
        else:
            category_name = ""

    if st.button("Generate and Publish"):
        if (
            keywords
            and topics
            and openai_api_key
            and wordpress_domain
            and admin_username
            and admin_password
            and category_name
        ):
            keywords = [keyword.strip() for keyword in keywords.split(",")]
            topics = [topic.strip() for topic in topics.split(",")]

            blog_articles = generate_blog_articles(
                keywords, topics, tone, openai_api_key
            )

            publish_articles_on_wordpress(
                blog_articles,
                category_name,
                wordpress_domain,
                admin_username,
                admin_password,
            )
        else:
            st.error(
                "Please fill out all fields before generating and publishing the articles."
            )


if __name__ == "__main__":
    main()
