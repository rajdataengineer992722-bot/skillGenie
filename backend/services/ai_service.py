import logging
import json

from openai import OpenAI

try:
    from backend.config import OPENAI_API_KEY
except ModuleNotFoundError:
    from config import OPENAI_API_KEY


logger = logging.getLogger(__name__)


ROLE_ARCHETYPES = [
    {
        "type": "student",
        "keywords": ["student", "class", "grade", "exam", "board", "neet", "jee", "school", "college"],
        "title_hint": "student exam-prep roadmap",
        "current_level": "Learner preparing for stronger concept mastery, practice quality, revision, and performance in tests or exams.",
        "time_available": "60 to 120 minutes a day depending on class schedule and exam pressure.",
        "focus_points": [
            "concept clarity",
            "chapter-wise practice",
            "revision strategy",
            "mistake correction",
            "exam confidence",
        ],
        "deliverables": "chapter notes, solved practice sets, revision sheets, and measurable score improvement.",
        "success_checks": "ability to solve independently, revise quickly, and perform better in timed tests.",
        "project_label": "STUDY OUTPUT",
        "project_points": [
            "Create a revision system with solved examples, weak-topic review, and timed practice.",
            "Show improvement through chapter completion, reduced mistakes, and stronger confidence.",
        ],
        "books": [
            "Make It Stick by Peter C. Brown | Why: Helps improve retention and revision quality.",
            "Atomic Habits by James Clear | Why: Useful for building consistent study systems.",
        ],
        "videos": [
            "Khan Academy topic lessons | Why: Clear concept explanations with worked examples.",
            "Exam-focused chapter revision videos | Why: Good for fast recap and question-solving practice.",
        ],
    },
    {
        "type": "teacher",
        "keywords": ["teacher", "faculty", "educator", "tutor", "mentor", "classroom", "lesson"],
        "title_hint": "teaching roadmap",
        "current_level": "Teaching-focused learner aiming to explain concepts clearly, structure lessons well, and improve student understanding.",
        "time_available": "45 to 90 minutes a day for lesson planning, review, worksheet design, and reflection.",
        "focus_points": [
            "lesson planning",
            "concept explanation",
            "example design",
            "student misconception handling",
            "assessment quality",
        ],
        "deliverables": "lesson plans, teaching aids, worksheets, and simple assessments.",
        "success_checks": "ability to teach clearly, engage students, and check understanding effectively.",
        "project_label": "TEACHING OUTPUT",
        "project_points": [
            "Create a complete lesson pack with explanation flow, examples, activities, worksheet, and assessment.",
            "Show how you would teach, evaluate understanding, and improve weak classroom moments.",
        ],
        "books": [
            "Teach Like a Champion by Doug Lemov | Why: Practical classroom techniques and teaching moves.",
            "Understanding by Design by Grant Wiggins and Jay McTighe | Why: Stronger lesson and assessment planning.",
        ],
        "videos": [
            "Classroom teaching strategy videos | Why: Helpful for live explanation and engagement ideas.",
            "Subject-specific pedagogy lessons | Why: Useful for turning content into teachable classroom steps.",
        ],
    },
    {
        "type": "developer",
        "keywords": ["developer", "engineer", "frontend", "backend", "full stack", "software", "react", "python", "java", "web"],
        "title_hint": "job-ready engineering roadmap",
        "current_level": "Builder-focused learner aiming to ship practical work, improve technical depth, and explain decisions clearly.",
        "time_available": "60 to 120 minutes a day for study, implementation, debugging, and project polish.",
        "focus_points": [
            "technical fundamentals",
            "real-world feature building",
            "system and product thinking",
            "debugging and iteration",
            "portfolio proof",
        ],
        "deliverables": "working features, projects, polished UX, case studies, and interview-ready explanations.",
        "success_checks": "ability to build, debug, explain tradeoffs, and present proof of work.",
        "project_label": "PROJECT",
        "project_points": [
            "Build a practical project that directly proves the target role and the stated goal.",
            "Show architecture choices, implementation quality, problem solving, and visible user value.",
        ],
        "books": [
            "The Pragmatic Programmer by David Thomas and Andrew Hunt | Why: Strong practical engineering judgment.",
            "Designing Data-Intensive Applications by Martin Kleppmann | Why: Useful when projects grow in complexity.",
        ],
        "videos": [
            "Fireship engineering videos | Why: Fast practical context and implementation ideas.",
            "Web Dev Simplified or similar build-focused tutorials | Why: Good for concrete project execution.",
        ],
    },
    {
        "type": "designer",
        "keywords": ["designer", "ui", "ux", "product design", "graphic", "visual design"],
        "title_hint": "design execution roadmap",
        "current_level": "Design-focused learner building stronger problem framing, interface quality, and portfolio presentation.",
        "time_available": "45 to 90 minutes a day for design study, critique, iteration, and case study work.",
        "focus_points": [
            "design fundamentals",
            "user flow thinking",
            "visual hierarchy",
            "iteration and critique",
            "portfolio storytelling",
        ],
        "deliverables": "wireframes, polished screens, design systems, and portfolio-ready case studies.",
        "success_checks": "ability to explain design choices, improve usability, and present a complete design process.",
        "project_label": "DESIGN OUTPUT",
        "project_points": [
            "Create a focused design case study with problem framing, user flow, interface exploration, and final screens.",
            "Show your reasoning, iteration path, and the value of the final design decisions.",
        ],
        "books": [
            "Refactoring UI by Adam Wathan and Steve Schoger | Why: Helps improve visual polish and interface quality.",
            "Don't Make Me Think by Steve Krug | Why: Strong usability and clarity fundamentals.",
        ],
        "videos": [
            "Design critique videos | Why: Useful for understanding what makes interfaces stronger.",
            "Figma workflow tutorials | Why: Helpful for faster practical execution.",
        ],
    },
    {
        "type": "analyst",
        "keywords": ["analyst", "data", "business analyst", "sql", "excel", "reporting", "analytics"],
        "title_hint": "analysis roadmap",
        "current_level": "Analytical learner aiming to move from raw data to useful insights and decision-ready communication.",
        "time_available": "45 to 90 minutes a day for data work, interpretation, and presentation practice.",
        "focus_points": [
            "data fundamentals",
            "querying and cleaning",
            "analysis workflow",
            "visualization",
            "insight communication",
        ],
        "deliverables": "clean datasets, analyses, dashboards, and concise business recommendations.",
        "success_checks": "ability to interpret data, communicate findings, and support decisions with evidence.",
        "project_label": "ANALYSIS OUTPUT",
        "project_points": [
            "Create an analysis case with cleaned data, key findings, visuals, and recommendations.",
            "Show how you moved from question to insight and what action the result supports.",
        ],
        "books": [
            "Storytelling with Data by Cole Nussbaumer Knaflic | Why: Makes analysis clearer and more persuasive.",
            "Naked Statistics by Charles Wheelan | Why: Good intuition for data interpretation.",
        ],
        "videos": [
            "SQL or data analysis walkthroughs | Why: Good for hands-on practice flow.",
            "Dashboard design tutorials | Why: Helps turn analysis into clearer communication.",
        ],
    },
    {
        "type": "manager",
        "keywords": ["manager", "lead", "product manager", "project manager", "leadership", "scrum", "agile"],
        "title_hint": "leadership and execution roadmap",
        "current_level": "Execution-focused learner building stronger planning, communication, prioritization, and team impact.",
        "time_available": "30 to 75 minutes a day for planning, reflection, execution systems, and stakeholder communication.",
        "focus_points": [
            "prioritization",
            "planning",
            "stakeholder communication",
            "execution quality",
            "decision making",
        ],
        "deliverables": "plans, briefs, meeting outcomes, retrospectives, and measurable execution improvements.",
        "success_checks": "ability to align people, prioritize work, and deliver outcomes with clarity.",
        "project_label": "EXECUTION OUTPUT",
        "project_points": [
            "Create a planning pack with goals, priorities, milestones, risks, and communication updates.",
            "Show better execution quality, clearer decisions, and stronger team alignment.",
        ],
        "books": [
            "High Output Management by Andrew Grove | Why: Strong execution and management fundamentals.",
            "The Making of a Manager by Julie Zhuo | Why: Helpful for practical leadership growth.",
        ],
        "videos": [
            "Product or project planning breakdowns | Why: Useful for execution structure and prioritization.",
            "Leadership communication talks | Why: Helps with alignment and influence.",
        ],
    },
    {
        "type": "marketing",
        "keywords": ["marketing", "seo", "content", "brand", "social media", "growth", "copywriter"],
        "title_hint": "marketing execution roadmap",
        "current_level": "Growth-focused learner aiming to understand audience, messaging, campaign structure, and measurable performance.",
        "time_available": "45 to 90 minutes a day for research, campaign planning, content, and review.",
        "focus_points": [
            "audience understanding",
            "messaging",
            "campaign execution",
            "content quality",
            "performance measurement",
        ],
        "deliverables": "content calendars, campaigns, landing pages, and performance reviews.",
        "success_checks": "ability to plan campaigns, improve messaging, and connect work to business outcomes.",
        "project_label": "CAMPAIGN OUTPUT",
        "project_points": [
            "Build a mini campaign plan with audience, messaging, channel strategy, assets, and metrics.",
            "Show how the work moves from idea to measurable result.",
        ],
        "books": [
            "Building a StoryBrand by Donald Miller | Why: Stronger messaging and positioning.",
            "Contagious by Jonah Berger | Why: Useful for understanding shareable ideas and audience behavior.",
        ],
        "videos": [
            "Marketing campaign teardown videos | Why: Helps connect theory to real execution.",
            "SEO or content strategy tutorials | Why: Useful for practical workflow and prioritization.",
        ],
    },
    {
        "type": "sales",
        "keywords": ["sales", "account executive", "business development", "bdm", "closing", "prospecting"],
        "title_hint": "sales performance roadmap",
        "current_level": "Sales-focused learner building stronger prospecting, discovery, communication, and closing discipline.",
        "time_available": "30 to 60 minutes a day for outreach systems, practice, reflection, and pipeline improvement.",
        "focus_points": [
            "prospecting",
            "discovery",
            "objection handling",
            "follow-up discipline",
            "closing confidence",
        ],
        "deliverables": "outreach scripts, call notes, pipeline improvements, and better conversion habits.",
        "success_checks": "ability to run clearer conversations, handle objections, and improve conversion quality.",
        "project_label": "SALES OUTPUT",
        "project_points": [
            "Create a sales playbook with outreach structure, discovery questions, objection responses, and follow-up cadence.",
            "Show stronger process consistency and clearer deal movement.",
        ],
        "books": [
            "SPIN Selling by Neil Rackham | Why: Strong discovery and sales conversation fundamentals.",
            "Fanatical Prospecting by Jeb Blount | Why: Useful for building consistent pipeline habits.",
        ],
        "videos": [
            "Sales call breakdowns | Why: Helpful for hearing how strong conversations are structured.",
            "Prospecting workflow tutorials | Why: Useful for building repeatable outreach systems.",
        ],
    },
]


def _get_client():
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY, timeout=12.0, max_retries=1)


def _persona_context(role: str, goal: str):
    combined = f"{role} {goal}".strip().lower()

    matched = next(
        (
            archetype
            for archetype in ROLE_ARCHETYPES
            if any(keyword in combined for keyword in archetype["keywords"])
        ),
        None,
    )

    if matched:
        return {key: value for key, value in matched.items() if key != "keywords"}

    return {
        "type": "general",
        "title_hint": "guided learning roadmap",
        "current_level": "Learner-focused path aimed at building practical skill, confidence, and visible progress.",
        "time_available": "45 to 90 minutes a day with steady weekly review.",
        "focus_points": [
            "fundamentals",
            "guided practice",
            "real-world application",
            "feedback and iteration",
            "proof of progress",
        ],
        "deliverables": "structured notes, practical exercises, and one clear proof-of-learning output.",
        "success_checks": "ability to apply the topic, explain it clearly, and improve through practice.",
        "project_label": "PROJECT",
        "project_points": [
            "Create one visible output that proves you can apply what you learned.",
            "Show progress from fundamentals to confident execution.",
        ],
        "books": [
            "Atomic Habits by James Clear | Why: Helps build reliable learning momentum.",
            "Make It Stick by Peter C. Brown | Why: Useful for stronger retention and practice quality.",
        ],
        "videos": [
            "High-quality guided topic lessons | Why: Useful for quickly understanding the basics.",
            "Practical walkthroughs for the topic | Why: Helps connect theory to action.",
        ],
    }


def _level_context(knowledge_level: str):
    normalized = (knowledge_level or "beginner").strip().lower()
    if normalized == "advanced":
        return {
            "label": "Advanced",
            "study_style": "prioritize deep reading, edge cases, tradeoffs, and advanced execution details",
            "practice_style": "focus on difficult scenarios, refinement, and performance under realistic constraints",
            "reading_depth": "assume strong basics and recommend higher-value material instead of introductory content",
        }
    if normalized == "intermediate":
        return {
            "label": "Intermediate",
            "study_style": "blend concept revision with applied reading and practical examples",
            "practice_style": "focus on turning working knowledge into consistency and stronger real-world application",
            "reading_depth": "assume partial familiarity and recommend material that fills gaps while improving execution",
        }
    return {
        "label": "Beginner",
        "study_style": "start with simple explanations, foundational reading, and guided examples",
        "practice_style": "focus on confidence-building, repetition, and smaller practice units",
        "reading_depth": "assume limited prior exposure and recommend beginner-friendly reading before harder material",
    }


def _fallback_learning_plan(role, goal, knowledge_level="beginner"):
    role_name = role.strip() or "Learner"
    goal_name = goal.strip() or "Build practical job-ready skills"
    persona = _persona_context(role_name, goal_name)
    level = _level_context(knowledge_level)

    return "\n".join(
        [
            f"ROLE: {role_name}",
            f"GOAL: {goal_name}",
            f"CURRENT LEVEL: {level['label']} learner. {persona['current_level']}",
            f"TIME AVAILABLE: {persona['time_available']}",
            f"SUMMARY: Build practical momentum toward becoming a stronger {role_name} with a clear weekly study rhythm for {goal_name}.",
            "WEEK 1: Sharpen the fundamentals",
            f"- Focus: Revisit the core concepts that directly support {goal_name}, especially {persona['focus_points'][0]}.",
            "- Why this matters: Strong fundamentals reduce confusion later and make projects easier to finish.",
            f"- Study: {level['study_style']}. Read the core ideas, key terms, and the most important first concepts before moving forward.",
            f"- Practice: {level['practice_style']}. Convert each concept into one note, one worked example, or one tiny applied task.",
            f"- Deliverable: A first working output focused on {persona['deliverables']}.",
            f"- Success Check: You show early progress in {persona['success_checks']}.",
            "WEEK 2: Build one practical mini-project",
            f"- Focus: Turn theory into structured practice related to {goal_name}, with emphasis on {persona['focus_points'][1]}.",
            "- Why this matters: Employers care more about applied understanding than passive study.",
            f"- Study: {level['reading_depth']}. Review how similar real-world examples are structured and note the most common mistakes.",
            "- Practice: Break the project into daily slices and ship one visible improvement each day.",
            f"- Deliverable: A stronger weekly output that reflects {persona['deliverables']}.",
            f"- Success Check: You can show visible growth in {persona['focus_points'][1]}.",
            "WEEK 3: Fix weak spots and improve quality",
            f"- Focus: Review gaps, improve quality, and strengthen {persona['focus_points'][2]}.",
            "- Why this matters: Quality and clarity separate tutorial work from real production-ready work.",
            "- Study: Learn the concepts behind testing, usability, maintainability, and good technical decisions.",
            "- Practice: Refactor one rough area, add tests or documentation, and rehearse explaining your decisions.",
            f"- Deliverable: A refined outcome that better demonstrates {persona['deliverables']}.",
            f"- Success Check: You improve on {persona['focus_points'][3]} and can explain what changed.",
            "WEEK 4: Package your proof of work",
            f"- Focus: Make your work job-ready for a {role_name} path.",
            "- Why this matters: You need visible proof that you can do the role, not just talk about it.",
            "- Study: Review hiring expectations, project storytelling, and the language needed for interviews.",
            "- Practice: Prepare portfolio bullets, interview stories, and one stretch improvement.",
            f"- Deliverable: Final proof package showing {persona['deliverables']}.",
            f"- Success Check: You meet the roadmap standard for {persona['success_checks']}.",
            "BOOKS:",
            f"- {persona['books'][0]}",
            f"- {persona['books'][1]}",
            "VIDEOS:",
            f"- {persona['videos'][0]}",
            f"- {persona['videos'][1]}",
            f"{persona['project_label']}:",
            f"- {persona['project_points'][0]}",
            f"- {persona['project_points'][1]}",
            "NEXT ACTION:",
            "- Spend 45 minutes today defining the first weekly deliverable and the smallest project you can finish this week.",
            "FOLLOW-UP QUESTIONS:",
            "- Turn this into a 7-day sprint.",
            "- Suggest the best first project for this roadmap.",
            "- Explain this plan for my current level in simpler language.",
        ]
    )


def _fallback_chat_response(message):
    clean_message = (message or "").strip()
    if not clean_message:
        return "\n".join(
            [
                "NOW:",
                "- Tell me your target role, your current level, and what feels hard right now.",
                "WHY:",
                "- That helps me give you a realistic next step instead of generic advice.",
                "TODAY:",
                "- Pick one topic, one practice block, and one small proof-of-work goal.",
                "BOOKS:",
                "- Atomic Habits by James Clear | Why: Useful if your biggest problem is consistency, not knowledge.",
                "VIDEOS:",
                "- Ali Abdaal study systems videos | Why: Helpful for improving learning systems and review habits.",
                "NEXT QUESTIONS:",
                "- Ask me for a 7-day sprint, one project idea, or a beginner-friendly explanation.",
            ]
        )

    return "\n".join(
        [
            "NOW:",
            f"- Focus on one concrete next move for: {clean_message[:120]}",
            "WHY:",
            "- You will make faster progress by reducing decision overload and shipping one useful outcome first.",
            "TODAY:",
            "- Study the core idea for 20 minutes, practice for 20 minutes, and write down one takeaway for 10 minutes.",
            "PROJECT:",
            "- Build a tiny proof-of-work that shows the concept in action instead of only reading about it.",
            "BOOKS:",
            "- The Pragmatic Programmer by David Thomas and Andrew Hunt | Why: Good for practical engineering judgment.",
            "VIDEOS:",
            "- Traversy Media project tutorials | Why: Useful when you need a concrete build sequence and implementation flow.",
            "WATCH OUT:",
            "- Do not jump between too many resources before finishing one focused exercise.",
            "NEXT QUESTIONS:",
            "- Ask me to turn this into a daily plan, a project brief, or an interview-ready explanation.",
        ]
    )


def _plan_prompt(role, goal, knowledge_level):
    persona = _persona_context(role, goal)
    level = _level_context(knowledge_level)
    return (
        "You are SkillGenie AI, a practical mentor who gives guided learning plans that feel like a real coach.\n"
        "Return plain text only. Use exactly these section headings in this order:\n"
        "ROLE:\n"
        "GOAL:\n"
        "CURRENT LEVEL:\n"
        "TIME AVAILABLE:\n"
        "SUMMARY:\n"
        "WEEK 1:\n"
        "- Focus:\n"
        "- Why this matters:\n"
        "- Study:\n"
        "- Practice:\n"
        "- Deliverable:\n"
        "- Success Check:\n"
        "WEEK 2:\n"
        "- Focus:\n"
        "- Why this matters:\n"
        "- Study:\n"
        "- Practice:\n"
        "- Deliverable:\n"
        "- Success Check:\n"
        "WEEK 3:\n"
        "- Focus:\n"
        "- Why this matters:\n"
        "- Study:\n"
        "- Practice:\n"
        "- Deliverable:\n"
        "- Success Check:\n"
        "WEEK 4:\n"
        "- Focus:\n"
        "- Why this matters:\n"
        "- Study:\n"
        "- Practice:\n"
        "- Deliverable:\n"
        "- Success Check:\n"
        "BOOKS:\n"
        "- <Title> by <Author> | Why: <reason>\n"
        "VIDEOS:\n"
        "- <Title> by <Channel> | Why: <reason>\n"
        "PROJECT:\n"
        "- What to build\n"
        "- What skills it proves\n"
        "NEXT ACTION:\n"
        "- <single best next step>\n"
        "FOLLOW-UP QUESTIONS:\n"
        "- <useful next question>\n"
        "Requirements:\n"
        f"- Choose the roadmap style for this persona: {persona['type']}.\n"
        f"- Prior knowledge level: {level['label']}.\n"
        f"- Study guidance should {level['study_style']}.\n"
        f"- Practice guidance should {level['practice_style']}.\n"
        f"- Reading suggestions should {level['reading_depth']}.\n"
        f"- Persona title hint: {persona['title_hint']}.\n"
        f"- Focus areas to prioritize: {', '.join(persona['focus_points'])}.\n"
        f"- Deliverables should feel like: {persona['deliverables']}.\n"
        f"- Success checks should reflect: {persona['success_checks']}.\n"
        f"- Use the section label `{persona['project_label']}:` exactly instead of a generic project label.\n"
        "- Be realistic and role-appropriate, not generic.\n"
        "- Mention practical deliverables, not vague study goals.\n"
        "- The `Study` line in each week must clearly say what the learner should read, review, or study next based on their current level.\n"
        "- Recommend 2 books and 2 videos max.\n"
        "- Make the roadmap feel like a strong ChatGPT-style learning coach response.\n"
        "- Make the plan feel useful for real learning, not generic motivation.\n"
        f"Role: {role}\n"
        f"Goal: {goal}"
    )


def _chat_prompt(message):
    return [
        {
            "role": "system",
            "content": (
                "You are SkillGenie AI, a grounded learning coach and career mentor.\n"
                "Give advice that sounds like a real mentor helping someone do the next useful thing.\n"
                "Return plain text only. Use these headings when relevant and keep the order:\n"
                "NOW:\nWHY:\nTODAY:\nPROJECT:\nBOOKS:\nVIDEOS:\nWATCH OUT:\nNEXT QUESTIONS:\n"
                "Requirements:\n"
                "- Give one practical next step first.\n"
                "- Prefer real-world solutions over generic theory.\n"
                "- Suggest at most 2 books and 2 videos.\n"
                "- Explain why each resource is worth the user's time.\n"
                "- Keep it concise, useful, and realistic."
            ),
        },
        {"role": "user", "content": message},
    ]


def _history_snippet(recent_messages):
    history = []
    for item in recent_messages or []:
        prompt = str(item.get("prompt", "")).strip()
        response = str(item.get("response", "")).strip()
        if prompt:
            history.append(f"User: {prompt[:220]}")
        if response:
            history.append(f"Coach: {response[:260]}")
    return "\n".join(history[-6:])


def _plan_snapshot(plan_text: str):
    lines = [line.strip() for line in str(plan_text or "").splitlines() if line.strip()]
    important = [
        line
        for line in lines
        if line.startswith("SUMMARY:")
        or line.startswith("WEEK 1:")
        or line.startswith("WEEK 2:")
        or line.startswith("NEXT ACTION:")
        or line.startswith("- Focus:")
        or line.startswith("- Deliverable:")
    ]
    return "\n".join(important[:8])


def _build_employee_plan_fallback(
    role: str,
    goal: str,
    knowledge_level: str,
    department: str = "",
    business_context: str = "",
    past_learning: str = "",
):
    role_name = role.strip() or "Employee"
    goal_name = goal.strip() or "improve role performance"
    persona = _persona_context(role_name, goal_name)
    level = _level_context(knowledge_level)
    context_line = business_context.strip() or "No specific business context provided."

    return {
        "title": f"{role_name} Roadmap For {goal_name}",
        "role": role_name,
        "goal": goal_name,
        "knowledge_level": level["label"],
        "department": department.strip() or "General",
        "summary": (
            f"A practical upskilling roadmap tailored for a {level['label'].lower()}-level {role_name}, "
            f"focused on {goal_name} and aligned to business outcomes."
        ),
        "business_impact": context_line,
        "past_learning_notes": past_learning.strip() or "No past learning details provided.",
        "skill_gap_analysis": [
            {
                "skill": persona["focus_points"][0],
                "current_level": "Developing",
                "target_level": "Confident execution",
                "priority": "High",
                "why": "This gap limits immediate role impact and confidence.",
            },
            {
                "skill": persona["focus_points"][1],
                "current_level": "Basic familiarity",
                "target_level": "Applied proficiency",
                "priority": "High",
                "why": "This skill is needed to turn learning into visible output.",
            },
            {
                "skill": persona["focus_points"][2],
                "current_level": "Inconsistent",
                "target_level": "Reliable quality",
                "priority": "Medium",
                "why": "Improves quality, consistency, and work credibility.",
            },
        ],
        "recommended_resources": {
            "internal": [
                {
                    "name": f"{department.strip() or 'Team'} knowledge base",
                    "type": "Internal doc",
                    "why": "Provides company-specific standards and workflows.",
                },
                {
                    "name": "Past project playbooks",
                    "type": "Internal reference",
                    "why": "Shows how similar work was executed successfully.",
                },
            ],
            "external": [
                {"name": persona["books"][0], "type": "Book"},
                {"name": persona["books"][1], "type": "Book"},
                {"name": persona["videos"][0], "type": "Video"},
                {"name": persona["videos"][1], "type": "Video"},
            ],
        },
        "weekly_plan": [
            {
                "week": 1,
                "focus": "Baseline and fundamentals",
                "study": f"{level['study_style']}. Review role-critical concepts and business terms.",
                "practice": "Apply one concept daily to a small internal or simulated task.",
                "deliverable": "Baseline notes plus one practical output.",
                "business_impact": "Faster onboarding and fewer avoidable mistakes.",
            },
            {
                "week": 2,
                "focus": "Applied execution",
                "study": f"{level['reading_depth']}. Study best-practice examples from similar work.",
                "practice": "Build one work-relevant task or mini-project from end to end.",
                "deliverable": "A completed practical task with clear before/after value.",
                "business_impact": "Direct contribution to team outcomes.",
            },
            {
                "week": 3,
                "focus": "Quality and skill-gap closure",
                "study": "Review weak areas and common failure patterns.",
                "practice": "Refine output quality and close top-priority gaps.",
                "deliverable": "Improved version with measurable quality gains.",
                "business_impact": "More reliable delivery and reduced rework.",
            },
            {
                "week": 4,
                "focus": "Scale and demonstrate impact",
                "study": "Learn advanced patterns and communication for stakeholder updates.",
                "practice": "Ship a role-aligned output and present outcomes.",
                "deliverable": "Final showcase artifact + measurable impact summary.",
                "business_impact": "Improved productivity and higher role confidence.",
            },
        ],
        "practice_tasks": [
            {
                "title": "Solve one real workflow bottleneck",
                "difficulty": "Medium",
                "estimated_hours": 4,
                "success_metric": "Reduce turnaround time or improve quality by at least 10%.",
            },
            {
                "title": "Build a reusable team asset",
                "difficulty": "Medium",
                "estimated_hours": 3,
                "success_metric": "At least one teammate can use the output without extra guidance.",
            },
            {
                "title": "Run one feedback loop",
                "difficulty": "Low",
                "estimated_hours": 2,
                "success_metric": "Capture feedback and apply at least two improvements.",
            },
        ],
        "mini_quiz": [
            {
                "question": "Which skill gap is currently the highest priority and why?",
                "answer_hint": "It should connect directly to near-term business impact.",
            },
            {
                "question": "What is one measurable outcome you can deliver this week?",
                "answer_hint": "Use a metric such as speed, quality, or error reduction.",
            },
            {
                "question": "How will you apply this learning to actual team work?",
                "answer_hint": "Map learning to one live workflow or project task.",
            },
        ],
        "next_action": "Schedule your first 60-minute focused block and complete one small, role-relevant output today.",
    }


def _plan_to_text(plan: dict) -> str:
    lines = [
        f"ROLE: {plan.get('role', '')}",
        f"GOAL: {plan.get('goal', '')}",
        f"CURRENT LEVEL: {plan.get('knowledge_level', '')}",
        f"TIME AVAILABLE: Weekly focused blocks aligned to team workload.",
        f"SUMMARY: {plan.get('summary', '')}",
    ]

    weekly = plan.get("weekly_plan", [])
    for week in weekly:
        lines.extend(
            [
                f"WEEK {week.get('week', '')}: {week.get('focus', 'Execution')}",
                f"- Focus: {week.get('focus', '')}",
                "- Why this matters: Builds practical role capability and measurable business impact.",
                f"- Study: {week.get('study', '')}",
                f"- Practice: {week.get('practice', '')}",
                f"- Deliverable: {week.get('deliverable', '')}",
                f"- Success Check: {week.get('business_impact', '')}",
            ]
        )

    lines.append("BOOKS:")
    for item in plan.get("recommended_resources", {}).get("external", []):
        name = item.get("name", "")
        if "book" in item.get("type", "").lower():
            lines.append(f"- {name}")

    lines.append("VIDEOS:")
    for item in plan.get("recommended_resources", {}).get("external", []):
        name = item.get("name", "")
        if "video" in item.get("type", "").lower():
            lines.append(f"- {name}")

    lines.append("PROJECT:")
    for task in plan.get("practice_tasks", [])[:2]:
        lines.append(f"- {task.get('title', '')} ({task.get('difficulty', '')})")

    lines.extend(
        [
            "NEXT ACTION:",
            f"- {plan.get('next_action', '')}",
            "FOLLOW-UP QUESTIONS:",
        ]
    )
    for quiz in plan.get("mini_quiz", [])[:3]:
        lines.append(f"- {quiz.get('question', '')}")

    return "\n".join(line for line in lines if line.strip())


def generate_learning_plan(
    role,
    goal,
    knowledge_level="beginner",
    department="",
    business_context="",
    past_learning="",
):
    client = _get_client()
    if not client:
        fallback = _build_employee_plan_fallback(
            role,
            goal,
            knowledge_level,
            department=department,
            business_context=business_context,
            past_learning=past_learning,
        )
        return {"plan_text": _plan_to_text(fallback), "structured_plan": fallback}

    try:
        prompt = (
            "You are an enterprise AI upskilling coach. Return ONLY valid JSON (no markdown).\n"
            "Generate a practical employee learning plan from role, goal, prior learning, and business context.\n"
            "JSON schema:\n"
            "{"
            "\"title\": str, \"role\": str, \"goal\": str, \"knowledge_level\": str, \"department\": str, "
            "\"summary\": str, \"business_impact\": str, \"past_learning_notes\": str, "
            "\"skill_gap_analysis\": [{\"skill\": str, \"current_level\": str, \"target_level\": str, \"priority\": \"High|Medium|Low\", \"why\": str}], "
            "\"recommended_resources\": {\"internal\": [{\"name\": str, \"type\": str, \"why\": str}], \"external\": [{\"name\": str, \"type\": str}]}, "
            "\"weekly_plan\": [{\"week\": int, \"focus\": str, \"study\": str, \"practice\": str, \"deliverable\": str, \"business_impact\": str}], "
            "\"practice_tasks\": [{\"title\": str, \"difficulty\": \"Low|Medium|High\", \"estimated_hours\": int, \"success_metric\": str}], "
            "\"mini_quiz\": [{\"question\": str, \"answer_hint\": str}], "
            "\"next_action\": str"
            "}\n"
            "Constraints:\n"
            "- Be specific, non-generic, and role-aware.\n"
            "- Study guidance must clearly state what to read/review for this knowledge level.\n"
            "- Internal resources should be workplace-oriented placeholders if actual company data is absent.\n"
            f"Role: {role}\n"
            f"Goal: {goal}\n"
            f"Knowledge level: {knowledge_level}\n"
            f"Department: {department}\n"
            f"Past learning: {past_learning}\n"
            f"Business context: {business_context}\n"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content or "{}"
        structured_plan = json.loads(content)
        plan_text = _plan_to_text(structured_plan)
        if not structured_plan or not plan_text.strip():
            raise ValueError("Empty structured plan response")
        return {"plan_text": plan_text, "structured_plan": structured_plan}
    except Exception as error:
        logger.exception("Learning plan generation failed; using fallback response: %s", error)
        fallback = _build_employee_plan_fallback(
            role,
            goal,
            knowledge_level,
            department=department,
            business_context=business_context,
            past_learning=past_learning,
        )
        return {"plan_text": _plan_to_text(fallback), "structured_plan": fallback}


def chat_response(message, role="", goal="", latest_plan_text="", recent_messages=None):
    client = _get_client()
    if not client:
        return _fallback_chat_response(message)

    try:
        context_message = (
            f"Known role: {role or 'Not provided'}\n"
            f"Known goal: {goal or 'Not provided'}\n"
            f"Latest plan snapshot:\n{_plan_snapshot(latest_plan_text) or 'No saved plan yet'}\n"
            f"Recent conversation:\n{_history_snippet(recent_messages) or 'No recent conversation yet'}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                _chat_prompt(message)[0],
                {"role": "system", "content": context_message},
                {"role": "user", "content": message},
            ],
        )
        return response.choices[0].message.content or _fallback_chat_response(message)
    except Exception as error:
        logger.exception("Chat response generation failed; using fallback response: %s", error)
        return _fallback_chat_response(message)
