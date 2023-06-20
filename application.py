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

            blog_articles.append(
                {
                    "title": title,
                    "article": article,
                }
            )

            time.sleep(5)

    return blog_articles


def publish_articles_on_wordpress(
    blog_articles, category_name, wordpress_domain, admin_username, admin_password
):
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

    category_id = get_category_id(category_name, wordpress_domain)

    if category_id is None:
        st.error(f"Failed to find category ID for category: {category_name}")
        return

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
            "categories": [category_id],
        }

        response = requests.post(url, json=data, headers=headers, verify=False)
        if response.status_code == 201:
            st.success(f"Article {i} published successfully!")
        else:
            st.error(f"Failed to publish Article {i}. Error: {response.text}")


def generate_title(keyword, topic, openai_api_key):
    prompt = f"Generate a title for a blog article about {keyword.strip()} and {topic.strip()}. Keep the title within 50 tokens."

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
    keywords = st.text_input("Keywords (separated by comma)")
    topics = st.text_input("Topics (separated by comma)")
    tone = st.selectbox("Tone", ["Funny", "Serious", "Informative"])

    if "openai_api_key" not in st.session_state:
        st.session_state["openai_api_key"] = st.text_input(
            "OpenAI API Key", type="password"
        )
    else:
        st.session_state["openai_api_key"] = st.text_input(
            "OpenAI API Key", value=st.session_state["openai_api_key"], type="password"
        )

    if "wordpress_domain" not in st.session_state:
        st.session_state["wordpress_domain"] = st.text_input("WordPress Domain")
    else:
        st.session_state["wordpress_domain"] = st.text_input(
            "WordPress Domain", value=st.session_state["wordpress_domain"]
        )

    if "admin_username" not in st.session_state:
        st.session_state["admin_username"] = st.text_input("WordPress Admin Username")
    else:
        st.session_state["admin_username"] = st.text_input(
            "WordPress Admin Username", value=st.session_state["admin_username"]
        )

    if "admin_password" not in st.session_state:
        st.session_state["admin_password"] = st.text_input(
            "WordPress Admin Password", type="password"
        )
    else:
        st.session_state["admin_password"] = st.text_input(
            "WordPress Admin Password",
            value=st.session_state["admin_password"],
            type="password",
        )

    categories = get_categories(st.session_state["wordpress_domain"])
    category_names = [category["name"] for category in categories]

    category_name = st.selectbox("Category", category_names)

    if st.button("Generate and Publish"):
        keywords = [keyword.strip() for keyword in keywords.split(",")]
        topics = [topic.strip() for topic in topics.split(",")]

        blog_articles = generate_blog_articles(
            keywords, topics, tone, st.session_state["openai_api_key"]
        )

        publish_articles_on_wordpress(
            blog_articles,
            category_name,
            st.session_state["wordpress_domain"],
            st.session_state["admin_username"],
            st.session_state["admin_password"],
        )


if __name__ == "__main__":
    main()
