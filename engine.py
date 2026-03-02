import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"

# ─────────────────────────────────────────────────────────────────
# COMPANY QUESTION BANKS
# Logic: Each company has 3 buckets:
#   "DSA"    → topic seeds for DSA/Company mode
#   "HR"     → actual HR question starters for HR mode
#   "coding" → specific coding problem patterns
#   "aptitude" → for companies that test aptitude (Capgemini, TCS, etc.)
#
# These are SEEDS injected into the system prompt.
# The LLM uses its training knowledge to expand them into full questions.
# Source: Commonly reported patterns from Glassdoor, GeeksForGeeks,
#         InterviewBit, and placement blogs — not fetched live.
# ─────────────────────────────────────────────────────────────────
COMPANY_QUESTION_BANKS = {
    "TCS": {
        "DSA":      ["Arrays and string manipulation", "Linked list reversal",
                     "Stack using queues", "Binary search variations",
                     "Basic sorting algorithms", "Pattern printing programs",
                     "Fibonacci with memoization", "Find duplicates in array", "Matrix rotation"],
        "HR":       ["Tell me about yourself", "Why TCS?",
                     "Where do you see yourself in 5 years?",
                     "Describe a team conflict", "Your biggest weakness", "Relocation willingness"],
        "coding":   ["Reverse a string without built-in functions",
                     "Find the second largest element in an array",
                     "Check if a number is palindrome"],
        "aptitude": ["Number series", "Time and work", "Profit and loss",
                     "Coding MCQs (output prediction)", "Verbal ability"]
    },

    "Infosys": {
        "DSA":      ["Recursion problems", "Binary trees traversal", "Hashing problems",
                     "Two-pointer technique", "Sliding window", "Graph BFS/DFS basics"],
        "HR":       ["Why Infosys?", "Agile methodology experience", "Handling work pressure",
                     "Leadership example", "Technical vs non-technical challenge"],
        "coding":   ["Implement a stack", "Find all permutations of a string",
                     "Detect cycle in linked list"],
        "aptitude": ["Logical reasoning", "Quantitative aptitude", "Verbal English",
                     "Puzzles", "Data interpretation"]
    },

    "Wipro": {
        "DSA":      ["Array rotation", "String anagram check", "Queue implementation",
                     "Tree height calculation", "Merge two sorted arrays"],
        "HR":       ["Why Wipro?", "Adaptability example", "Strength and weakness",
                     "Experience with deadlines", "Team player example"],
        "coding":   ["Reverse words in a sentence", "Find GCD of two numbers",
                     "Check balanced parentheses"],
        "aptitude": ["Quantitative reasoning", "Logical sequences", "English grammar",
                     "Basic coding MCQs"]
    },

    "Capgemini": {
        # Capgemini has a very specific hiring process:
        # Round 1: Pseudo code test (NOT actual coding — read pseudocode, predict output)
        # Round 2: Game-based aptitude (AMCAT/Cocubes — attention, memory, problem solving)
        # Round 3: English communication (grammar, essay, spoken)
        # Round 4: Technical + HR interview
        "DSA":      ["Pseudocode output prediction", "Algorithm flowchart reading",
                     "Time complexity identification from pseudocode",
                     "Basic OOP concepts (class, object, inheritance, polymorphism)",
                     "DBMS basics (normalization, SQL queries)",
                     "OS concepts (process, thread, deadlock)",
                     "Basic networking (OSI layers, TCP/IP)"],
        "HR":       ["Why Capgemini?", "Comfortable with service-based work?",
                     "Relocation and shift flexibility", "Describe yourself in 3 words",
                     "Tell me about a project you built", "Teamwork and communication example",
                     "How do you handle criticism?"],
        "coding":   ["Write pseudocode for bubble sort",
                     "Predict output of given pseudocode snippet",
                     "Identify error in pseudocode"],
        "aptitude": ["Game-based attention tasks", "Memory sequence games",
                     "Logical pattern recognition", "English grammar MCQs",
                     "Essay writing (150-200 words)", "Spoken English fluency",
                     "Vocabulary and reading comprehension"]
    },

    "Amazon": {
        "DSA":      ["Two Sum / K-Sum variants", "LRU Cache design", "Merge intervals",
                     "Trapping rainwater", "Sliding window maximum", "Word ladder BFS",
                     "Serialize/deserialize binary tree", "Course schedule (topological sort)",
                     "Design HashMap from scratch", "Longest substring without repeating chars"],
        "HR":       ["Tell me about a time you failed (Learn and Be Curious)",
                     "Most challenging project (Ownership)",
                     "Disagree with manager (Have Backbone)",
                     "Delivered results under pressure (Deliver Results)",
                     "Customer obsession example", "Invent and simplify example"],
        "coding":   ["Implement LRU cache using HashMap + Doubly Linked List",
                     "Find median from data stream", "Design parking lot system"]
    },

    "Google": {
        "DSA":      ["Dynamic programming (knapsack, LCS, LIS)", "Graph shortest paths (Dijkstra)",
                     "Trie implementation", "Segment trees", "Union-Find",
                     "System design (URL shortener, search engine)",
                     "Advanced string algorithms (KMP, Rabin-Karp)",
                     "Network flow problems", "Bit manipulation tricks"],
        "HR":       ["Biggest technical challenge overcome", "Handling ambiguity",
                     "Collaboration on large codebase", "Googleyness — curiosity example",
                     "Impact at scale"],
        "coding":   ["Design Google Docs (concurrency)", "Implement autocomplete with Trie",
                     "Find K closest points to origin"]
    },

    "Microsoft": {
        "DSA":      ["Binary tree problems (LCA, diameter)", "Graph coloring", "DP on strings",
                     "Design patterns (Singleton, Factory)", "OOP principles in code",
                     "Linked list merge and sort", "Stack/Queue design problems"],
        "HR":       ["Why Microsoft?", "Growth mindset example", "Cross-team collaboration",
                     "Most impactful project", "How you handle feedback"],
        "coding":   ["Clone a graph", "Design a cache system", "Implement Excel VLOOKUP"]
    },

    "Accenture": {
        "DSA":      ["Basic sorting", "Array manipulation", "String reversal",
                     "Simple recursion", "Fibonacci series"],
        "HR":       ["Why Accenture?", "Teamwork example", "Client handling mindset",
                     "Flexibility to travel/relocate", "Communication skills example"],
        "coding":   ["Swap two numbers without temp variable",
                     "Find missing number in array 1 to N",
                     "Count vowels in a string"],
        "aptitude": ["Logical reasoning", "Quantitative aptitude", "Attention to detail",
                     "Communication assessment"]
    }
}

# ─────────────────────────────────────────────────────────────────
# COMPANY OPENING QUESTIONS
# Logic: Each company has a UNIQUE first question that matches
#        their actual Round 1 interview style — not a generic opener.
# ─────────────────────────────────────────────────────────────────
COMPANY_OPENERS = {
    "Capgemini": {
        "Company": (
            "Let's simulate a real **Capgemini** interview! 🎯\n\n"
            "Capgemini's process has 4 stages:\n"
            "1️⃣ **Pseudo Code Test** → Read pseudocode, predict output\n"
            "2️⃣ **Game-Based Aptitude** → Attention, memory, pattern tasks\n"
            "3️⃣ **English Communication** → Grammar, essay, spoken fluency\n"
            "4️⃣ **Technical + HR Interview**\n\n"
            "Let's start with **Round 1 — Pseudo Code.**\n\n"
            "**PROMPT:** What will be the output of this pseudocode?\n"
            "```\nSET x = 10\nSET y = 3\nSET z = x MOD y\nIF z == 0 THEN\n"
            "   PRINT 'Divisible'\nELSE\n   PRINT z\nEND IF\n```"
        ),
        "DSA": (
            "Let's prep DSA for **Capgemini**! 🚀\n\n"
            "Capgemini focuses on **pseudocode, OOP, DBMS, and OS basics** — not heavy DSA.\n\n"
            "**PROMPT:** In Capgemini's technical round, they often test OOP. "
            "Can you explain the 4 pillars of OOP with a real-world example for each?"
        ),
        "HR": (
            "Welcome to your **Capgemini HR mock interview**! 🎤\n\n"
            "Capgemini HR is friendly but checks communication clarity and cultural fit.\n\n"
            "**PROMPT:** Tell me about yourself — focus on your communication skills "
            "and why you're a good fit for a service-based company like Capgemini."
        ),
        "Resume": (
            "Let's strengthen your resume for **Capgemini**! 📄\n\n"
            "Capgemini recruiters look for: projects, internships, communication, and adaptability.\n\n"
            "**PROMPT:** Share your strongest resume bullet or project description "
            "and we'll make it Capgemini-ready."
        )
    },
    "TCS": {
        "Company": (
            "Let's simulate a real **TCS** interview! 🎯\n\n"
            "TCS NQT has 3 sections:\n"
            "1️⃣ **Numerical Ability** → Arithmetic, algebra\n"
            "2️⃣ **Verbal Ability** → Grammar, comprehension\n"
            "3️⃣ **Reasoning + Coding** → Output prediction, basic coding\n\n"
            "**PROMPT:** TCS Coding Round — What is the output of this code?\n"
            "```python\nfor i in range(1, 6):\n    if i % 2 == 0:\n        print(i * 2)\n```"
        ),
        "DSA": (
            "Let's start DSA prep for **TCS**! 🚀\n\n"
            "**PROMPT:** TCS often starts with array basics. "
            "Given an array [3, 1, 4, 1, 5, 9, 2, 6], how would you find the second largest element? "
            "What is the time complexity of your approach?"
        ),
        "HR": (
            "Welcome to your **TCS HR mock interview**! 🎤\n\n"
            "**PROMPT:** Tell me about yourself — keep it under 2 minutes."
        ),
        "Resume": (
            "Let's strengthen your resume for **TCS**! 📄\n\n"
            "**PROMPT:** Share your best project bullet point and we'll make it TCS-ready."
        )
    },
    "Amazon": {
        "Company": (
            "Let's simulate a real **Amazon SDE** interview! 🎯\n\n"
            "Amazon interviews have 2 parts in every round:\n"
            "1️⃣ **DSA Problem** → Medium to Hard LeetCode\n"
            "2️⃣ **Leadership Principle** → Behavioral question\n\n"
            "**PROMPT:** Amazon Round 1 — DSA: Given an array of integers, "
            "find two numbers that add up to a target sum. "
            "What data structure would you use and what is the time complexity?"
        ),
        "DSA": (
            "Let's start DSA prep for **Amazon**! 🚀\n\n"
            "**PROMPT:** Amazon loves sliding window problems. "
            "Given a string, find the length of the longest substring without repeating characters. "
            "Walk me through your approach."
        ),
        "HR": (
            "Welcome to your **Amazon Leadership Principles** mock interview! 🎤\n\n"
            "Amazon evaluates every answer against their 16 Leadership Principles.\n\n"
            "**PROMPT:** Tell me about a time you took ownership of a project that wasn't going well. "
            "What did you do and what was the outcome? (Use STAR format)"
        ),
        "Resume": (
            "Let's strengthen your resume for **Amazon**! 📄\n\n"
            "**PROMPT:** Share your most impactful project bullet. "
            "Amazon recruiters want to see scale, ownership, and measurable impact."
        )
    }
}

# Default opener for companies not in COMPANY_OPENERS
DEFAULT_OPENERS = {
    "Company": lambda company, cdata, first_topic: (
        f"Let's simulate a real **{company}** interview! 🎯\n\n"
        f"Key focus areas: {', '.join(cdata.get('focus', [])[:3])}\n"
        f"Interview rounds: {' → '.join(cdata.get('rounds', ['Technical', 'HR']))}\n\n"
        f"**PROMPT:** {company} — {cdata.get('rounds', ['Technical Round'])[0]}: "
        f"{first_topic}. Walk me through your approach step by step."
    ),
    "DSA": lambda company, cdata, first_topic: (
        f"Let's start DSA prep for **{company}**! 🚀\n\n"
        f"**PROMPT:** {company} interviews often start with fundamentals. "
        f"Can you explain the difference between an Array and a Linked List? "
        f"When would you prefer one over the other?"
    ),
    "HR": lambda company, cdata, first_topic: (
        f"Welcome to your **{company} HR mock interview**! 🎤\n\n"
        f"**PROMPT:** Tell me about yourself — keep it under 2 minutes and tailor it for {company}."
    ),
    "Resume": lambda company, cdata, first_topic: (
        f"Let's strengthen your resume for **{company}**! 📄\n\n"
        f"**PROMPT:** Share your best project or resume bullet and we'll make it {company}-recruiter-proof."
    )
}

SYSTEM_PROMPTS = {
    "DSA": """You are a strict but friendly DSA interview coach using REACT PROMPTING.

After every student response you MUST follow this exact 3-step structure:

**REACT:** (1 line — praise or point out what was wrong/missing)
**ANALYZE:** (1 line — identify the exact gap or next concept to drill)
**PROMPT:** (ask ONE sharp follow-up question to go deeper)

Rules:
- Never give away full answers. Guide, don't lecture.
- If student is stuck, give a small hint and re-ask.
- Adapt difficulty based on their answers.
- Prioritize these company-specific topics: {company_questions}
- General topics: Arrays, Strings, Linked Lists, Trees, Graphs, DP, Sorting, Searching.

Student Profile: {profile}
Target Company: {company}
Company Focus Areas: {focus}
""",

    "HR": """You are an experienced HR interviewer using REACT PROMPTING.

After every student answer you MUST follow this exact 3-step structure:

**REACT:** (1 line — evaluate their answer quality, confidence, clarity)
**ANALYZE:** (1 line — what was missing: specifics, STAR format, confidence, etc.)
**PROMPT:** (ask ONE follow-up HR question — go deeper or move to next topic)

Rules:
- Evaluate answers on: Clarity, Confidence, Relevance, STAR format
- Prioritize these {company}-specific HR questions: {company_questions}
- Be realistic — don't be too easy or too harsh.
- If answer is vague, push for specifics.

Student Profile: {profile}
Target Company: {company}
""",

    "Company": """You are a placement coach specializing in {company}-specific prep using REACT PROMPTING.

After every student answer you MUST follow this exact 3-step structure:

**REACT:** (1 line — evaluate based on what {company} specifically expects)
**ANALYZE:** (1 line — identify gap vs. what {company} looks for)
**PROMPT:** (ask ONE question that mirrors actual {company} interview patterns)

Rules:
- Strictly simulate {company}'s interview style and difficulty level.
- Draw questions ONLY from {company}'s known patterns: {company_questions}
- Mention round context (e.g., "In {company}'s Pseudo Code Round..." or "In {company}'s Technical Round 1...")
- Give company-specific tips when student is stuck.
- For Capgemini: focus on pseudocode, OOP, English communication, game-based aptitude.
- For TCS: focus on output prediction, basic coding, NQT pattern.
- For Amazon: always pair DSA question with a Leadership Principle question.

Student Profile: {profile}
Company Rounds: {rounds}
Company Focus: {focus}
Company Tip: {tip}
""",

    "Resume": """You are a senior tech recruiter reviewing resumes using REACT PROMPTING.

After every resume bullet or experience the student shares, follow this 3-step structure:

**REACT:** (1 line — what's strong or weak about this bullet/project)
**ANALYZE:** (1 line — what's missing: metrics, action verbs, impact, clarity)
**PROMPT:** (ask ONE question to extract better content OR suggest a rewrite and ask them to improve it)

Rules:
- Push for quantified achievements (numbers, percentages, scale)
- Check for strong action verbs (Built, Optimized, Reduced, Led, Designed)
- Flag buzzwords with no substance
- Help them rewrite weak bullets into strong ones
- Tailor feedback to what {company} recruiters specifically look for

Student Profile: {profile}
Target Company: {company}
"""
}


def build_system_prompt(mode, profile, company, company_data):
    template = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["DSA"])
    focus    = ", ".join(company_data.get("focus", []))
    rounds   = ", ".join(company_data.get("rounds", []))
    tip      = company_data.get("tip", "")

    # Pull company-specific question seeds
    bank = COMPANY_QUESTION_BANKS.get(company, {})
    if mode == "HR":
        company_questions = "; ".join(bank.get("HR", ["Standard HR questions"]))
    elif mode == "Company":
        # For Company mode: mix DSA + coding + aptitude seeds
        seeds = bank.get("DSA", []) + bank.get("coding", []) + bank.get("aptitude", [])
        company_questions = "; ".join(seeds) if seeds else f"Standard {company} interview questions"
    else:
        company_questions = "; ".join(bank.get("DSA", ["Standard DSA topics"]))

    return template.format(
        profile=profile_to_text(profile),
        company=company,
        focus=focus,
        rounds=rounds,
        tip=tip,
        company_questions=company_questions
    )


def profile_to_text(profile):
    return (
        f"Name: {profile.get('name', 'Student')} | "
        f"Branch: {profile.get('branch', 'CS')} | "
        f"CGPA: {profile.get('cgpa', 'N/A')} | "
        f"Skills: {profile.get('skills', 'Python, DSA')} | "
        f"Year: {profile.get('year', 'Final Year')}"
    )


def get_opening_question(mode, company, company_data):
    # Check if this company has a custom opener
    if company in COMPANY_OPENERS and mode in COMPANY_OPENERS[company]:
        return COMPANY_OPENERS[company][mode]

    # Otherwise use the smart default
    bank        = COMPANY_QUESTION_BANKS.get(company, {})
    first_topic = bank.get("DSA", ["Explain your strongest technical topic"])[0]
    opener_fn   = DEFAULT_OPENERS.get(mode, DEFAULT_OPENERS["DSA"])
    return opener_fn(company, company_data, first_topic)


def react_prompt(user_message, history, system_prompt):
    messages = [{"role": "system", "content": system_prompt}] + history + [
        {"role": "user", "content": user_message}
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content


def generate_session_summary(history, profile, company, mode):
    # Guard: need at least one user answer
    user_msgs = [m for m in history if m["role"] == "user"]
    if not user_msgs:
        return "⚠️ No answers were recorded. Please answer at least one question before submitting."

    answered = len(user_msgs)
    summary_prompt = (
        f"You are a senior placement coach and technical interviewer.\n"
        f"The student completed a {mode} mock interview for {company}.\n"
        f"They answered {answered} question(s). Student: {profile_to_text(profile)}\n\n"
        f"CRITICAL: Even if only 1 question was answered, generate a FULL detailed report. "
        f"Never say 'not enough data'. Always produce every section below.\n\n"
        f"## Overall Performance\n"
        f"Write 3-4 honest lines about their performance, communication, and depth.\n\n"
        f"## Strengths Identified\n"
        f"List strengths with specific examples from their actual answers.\n"
        f"Format: - **[Strength]:** [Example from their answer]\n\n"
        f"## Weak Areas and Mistakes\n"
        f"List every gap or shallow answer with what was wrong and what was expected.\n"
        f"Format: - **[Weak Area]:** [What they said vs what was expected]\n\n"
        f"## Topic-wise Performance\n"
        f"Rate every topic covered (minimum 1 row):\n"
        f"| Topic | Score | Remarks |\n"
        f"|-------|-------|---------|\n"
        f"| [topic] | X/5 | [one line] |\n\n"
        f"## Personalized 3-Day Study Plan\n"
        f"**Day 1 - [Focus]:** specific tasks and resources\n"
        f"**Day 2 - [Focus]:** specific tasks and resources\n"
        f"**Day 3 - Mock Practice:** tailored suggestions for {company}\n\n"
        f"## {company}-Specific Tips\n"
        f"Give 3 actionable tips for cracking {company}\'s {mode} round.\n\n"
        f"## Readiness Score\n"
        f"**Overall Score: X/10**\n"
        f"- Communication: X/10\n"
        f"- Confidence: X/10\n"
        f"- Relevance of Answers: X/10\n"
        f"- {company} Readiness: X/10\n\n"
        f"**Verdict:** One honest sentence — ready for {company} or not?\n\n"
        f"RULES:\n"
        f"- Reference the actual answers given in the conversation\n"
        f"- For HR mode: evaluate STAR format, storytelling, clarity, confidence\n"
        f"- Be honest, do not inflate scores\n"
        f"- Produce ALL sections regardless of how many questions were answered"
    )
    try:
        messages = [{"role": "system", "content": summary_prompt}] + history
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=1500
        )
        result = response.choices[0].message.content
        if not result or not result.strip():
            return "⚠️ Summary came back empty. Please click Retry."
        return result
    except Exception as e:
        return f"⚠️ Could not generate summary: {str(e)}\n\nCheck your GROQ_API_KEY and try again."