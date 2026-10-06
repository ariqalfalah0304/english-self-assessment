"""
Sample question seed helper for testing and initial platform execution.
Populates standard Grammar and Reading questions if tables are empty.
"""

import sqlite3
from database.models import Question, Passage
from database import queries


SAMPLE_GRAMMAR_QUESTIONS = [
    # EASY LEVEL
    {
        "question_text": "The students ___ English every day in the classroom.",
        "option_a": "study",
        "option_b": "studies",
        "option_c": "studying",
        "option_d": "has studied",
        "correct_answer": "A",
        "explanation": "The subject 'students' is plural, so the simple present plural verb 'study' is required.",
        "difficulty": "Easy",
        "topic": "Subject-Verb Agreement",
    },
    {
        "question_text": "She ___ to school by bicycle yesterday morning.",
        "option_a": "go",
        "option_b": "goes",
        "option_c": "went",
        "option_d": "gone",
        "correct_answer": "C",
        "explanation": "'Yesterday morning' indicates simple past tense, so the irregular past verb 'went' is correct.",
        "difficulty": "Easy",
        "topic": "Simple Past Tense",
    },
    {
        "question_text": "They ___ always excited about learning new languages.",
        "option_a": "is",
        "option_b": "are",
        "option_c": "was",
        "option_d": "be",
        "correct_answer": "B",
        "explanation": "'They' is a plural subject pronoun requiring the plural linking verb 'are' in the present tense.",
        "difficulty": "Easy",
        "topic": "Subject-Verb Agreement",
    },
    {
        "question_text": "My father ___ coffee every morning before work.",
        "option_a": "drink",
        "option_b": "drinks",
        "option_c": "drinking",
        "option_d": "drank",
        "correct_answer": "B",
        "explanation": "'My father' is a third-person singular subject, which takes 'drinks' in simple present.",
        "difficulty": "Easy",
        "topic": "Simple Present Tense",
    },
    {
        "question_text": "We did not ___ the movie last night because we were tired.",
        "option_a": "watched",
        "option_b": "watching",
        "option_c": "watch",
        "option_d": "watches",
        "correct_answer": "C",
        "explanation": "After the auxiliary 'did not', the main verb must appear in its base form ('watch').",
        "difficulty": "Easy",
        "topic": "Auxiliary Verbs",
    },
    {
        "question_text": "Look! The baby is ___ peacefully in the crib.",
        "option_a": "sleep",
        "option_b": "sleeps",
        "option_c": "slept",
        "option_d": "sleeping",
        "correct_answer": "D",
        "explanation": "The auxiliary 'is' combined with an ongoing action requires the present participle 'sleeping'.",
        "difficulty": "Easy",
        "topic": "Present Continuous",
    },
    {
        "question_text": "There ___ three books on the wooden table.",
        "option_a": "is",
        "option_b": "are",
        "option_c": "was",
        "option_d": "has",
        "correct_answer": "B",
        "explanation": "'Three books' is plural, requiring the plural present verb 'are' after 'there'.",
        "difficulty": "Easy",
        "topic": "Subject-Verb Agreement",
    },
    {
        "question_text": "This apple is ___ than that one in the basket.",
        "option_a": "sweet",
        "option_b": "sweeter",
        "option_c": "sweetest",
        "option_d": "more sweet",
        "correct_answer": "B",
        "explanation": "Comparing two items using 'than' requires the comparative form 'sweeter'.",
        "difficulty": "Easy",
        "topic": "Comparatives",
    },

    # MEDIUM LEVEL
    {
        "question_text": "Neither the teacher nor the students ___ informed about the schedule change.",
        "option_a": "was",
        "option_b": "were",
        "option_c": "is",
        "option_d": "has been",
        "correct_answer": "B",
        "explanation": "In 'neither... nor' constructions, the verb agrees with the subject closer to it ('students', which is plural).",
        "difficulty": "Medium",
        "topic": "Proximity Agreement",
    },
    {
        "question_text": "By the time the guests arrived, Sarah ___ cooking dinner.",
        "option_a": "finished",
        "option_b": "has finished",
        "option_c": "had finished",
        "option_d": "finishes",
        "correct_answer": "C",
        "explanation": "An action completed before another past event requires the past perfect tense ('had finished').",
        "difficulty": "Medium",
        "topic": "Past Perfect Tense",
    },
    {
        "question_text": "If I ___ you, I would consult an academic advisor immediately.",
        "option_a": "was",
        "option_b": "am",
        "option_c": "were",
        "option_d": "would be",
        "correct_answer": "C",
        "explanation": "The second conditional hypothetical mood uses the subjunctive 'were' for all persons.",
        "difficulty": "Medium",
        "topic": "Conditionals",
    },
    {
        "question_text": "The committee ___ submitted its annual evaluation report yesterday.",
        "option_a": "has",
        "option_b": "have",
        "option_c": "had",
        "option_d": "having",
        "correct_answer": "A",
        "explanation": "When a collective noun functions as a single unified entity (emphasized by 'its'), it takes a singular verb.",
        "difficulty": "Medium",
        "topic": "Collective Nouns",
    },
    {
        "question_text": "Despite ___ thoroughly, he felt anxious before the chemistry exam.",
        "option_a": "prepare",
        "option_b": "he prepared",
        "option_c": "having prepared",
        "option_d": "prepared",
        "correct_answer": "C",
        "explanation": "The preposition 'despite' must be followed by a noun phrase or gerund phrase ('having prepared').",
        "difficulty": "Medium",
        "topic": "Prepositions & Gerunds",
    },
    {
        "question_text": "The laptop ___ screen was cracked during transit has been returned.",
        "option_a": "which",
        "option_b": "whose",
        "option_c": "that",
        "option_d": "whom",
        "correct_answer": "B",
        "explanation": "The possessive relative pronoun 'whose' refers to the laptop possessing the screen.",
        "difficulty": "Medium",
        "topic": "Relative Clauses",
    },
    {
        "question_text": "Scarcely ___ the auditorium when the keynote lecture began.",
        "option_a": "we had entered",
        "option_b": "had we entered",
        "option_c": "did we enter",
        "option_d": "have we entered",
        "correct_answer": "B",
        "explanation": "Negative/restrictive adverbs like 'scarcely' placed at sentence beginnings trigger subject-auxiliary inversion.",
        "difficulty": "Medium",
        "topic": "Inversion",
    },
    {
        "question_text": "She insisted that the meeting ___ postponed until next Monday.",
        "option_a": "is",
        "option_b": "was",
        "option_c": "be",
        "option_d": "would be",
        "correct_answer": "C",
        "explanation": "Verbs of demand/insistence require the subjunctive base form ('be') in the that-clause.",
        "difficulty": "Medium",
        "topic": "Subjunctive Mood",
    },

    # HARD LEVEL
    {
        "question_text": "Not only ___ the national science scholarship, but she also secured an international research grant.",
        "option_a": "she won",
        "option_b": "did she win",
        "option_c": "she did win",
        "option_d": "won she",
        "correct_answer": "B",
        "explanation": "'Not only' at the start of a clause requires negative inversion ('did she win').",
        "difficulty": "Hard",
        "topic": "Inversion & Correlative Conjunctions",
    },
    {
        "question_text": "Had the meteorologists forecasted the storm accurately, the coastal residents ___ earlier.",
        "option_a": "would evacuate",
        "option_b": "will have evacuated",
        "option_c": "would have evacuated",
        "option_d": "had evacuated",
        "correct_answer": "C",
        "explanation": "Inverted third conditional ('Had they forecasted...') requires 'would have + past participle' in the main clause.",
        "difficulty": "Hard",
        "topic": "Conditional Inversion",
    },
    {
        "question_text": "It is essential that each participant ___ their identification badge at the checkpoint.",
        "option_a": "displays",
        "option_b": "display",
        "option_c": "displayed",
        "option_d": "is displaying",
        "correct_answer": "B",
        "explanation": "Mandative subjunctive following 'essential that' requires the uninflected base verb ('display').",
        "difficulty": "Hard",
        "topic": "Mandative Subjunctive",
    },
    {
        "question_text": "The research findings, along with supplementary data from three laboratories, ___ published tomorrow.",
        "option_a": "is to be",
        "option_b": "are to be",
        "option_c": "will being",
        "option_d": "was to be",
        "correct_answer": "B",
        "explanation": "Parenthetical phrases ('along with...') do not alter the head subject ('findings', plural), requiring 'are to be'.",
        "difficulty": "Hard",
        "topic": "Intervening Phrases",
    },
    {
        "question_text": "___ known about the sudden road closure, we would have taken the bypass highway.",
        "option_a": "If we",
        "option_b": "Were we to",
        "option_c": "Had we",
        "option_d": "Did we",
        "correct_answer": "C",
        "explanation": "'Had we known' is the inverted past perfect form of 'If we had known'.",
        "difficulty": "Hard",
        "topic": "Conditional Inversion",
    },
    {
        "question_text": "Rarely ___ such unprecedented technological disruption occurred in so brief a period.",
        "option_a": "has",
        "option_b": "have",
        "option_c": "was",
        "option_d": "did",
        "correct_answer": "A",
        "explanation": "Negative adverbial 'Rarely' triggers inversion; the singular subject 'disruption' agrees with auxiliary 'has'.",
        "difficulty": "Hard",
        "topic": "Subject-Auxiliary Inversion",
    },
]


SAMPLE_READING_PASSAGES = [
    # 1. EASY PASSAGE
    {
        "title": "The Remarkable Life of Honeybees",
        "difficulty": "Easy",
        "passage_text": """Honeybees are social insects known for their crucial role in pollination and the production of honey. A single honeybee colony typically houses tens of thousands of bees organized into three distinct castes: the queen, drones, and worker bees. The queen is the sole fertile female responsible for laying eggs, while male drones exist primarily to mate with new queens.

Worker bees, all of whom are non-reproductive females, perform every essential task required to sustain the hive. Young workers clean the comb, feed larvae, and tend to the queen. As they mature, workers venture outside to forage for nectar and pollen from flowering plants. During foraging, pollen grains attach to their fuzzy bodies and are transferred between flowers, enabling plant reproduction. Without honeybees, countless agricultural crops and wildflowers would struggle to survive.""",
        "questions": [
            {
                "question_text": "What is the primary topic of the passage?",
                "question_type": "Main Idea",
                "option_a": "The production and commercial sale of honey",
                "option_b": "The social organization and pollination role of honeybees",
                "option_c": "Methods for preventing colony collapse in modern hives",
                "option_d": "The mating rituals of queen bees and male drones",
                "correct_answer": "B",
                "explanation": "The entire passage discusses how honeybees are organized in colonies and their vital role in pollinating flowers.",
            },
            {
                "question_text": "According to the passage, which group of bees is responsible for cleaning the hive and foraging for nectar?",
                "question_type": "Detail",
                "option_a": "The queen bee",
                "option_b": "Worker bees",
                "option_c": "Male drones",
                "option_d": "Larvae",
                "correct_answer": "B",
                "explanation": "Paragraph 2 explicitly states that worker bees perform every essential task, including cleaning the comb and foraging.",
            },
            {
                "question_text": "The word 'crucial' in the first sentence is closest in meaning to:",
                "question_type": "Vocabulary",
                "option_a": "optional",
                "option_b": "dangerous",
                "option_c": "essential",
                "option_d": "complicated",
                "correct_answer": "C",
                "explanation": "'Crucial' means extremely important or essential to the outcome.",
            },
            {
                "question_text": "In the second paragraph, the word 'they' refers to:",
                "question_type": "Reference",
                "option_a": "flowering plants",
                "option_b": "pollen grains",
                "option_c": "honeybee queens",
                "option_d": "worker bees",
                "correct_answer": "D",
                "explanation": "'As they mature' follows the discussion of worker bees and describes their transition to outdoor foraging.",
            },
        ],
    },

    # 2. MEDIUM PASSAGE
    {
        "title": "The Global Transition to Solar Energy",
        "difficulty": "Medium",
        "passage_text": """Over the past decade, solar photovoltaic (PV) technology has transformed from a niche clean-energy alternative into one of the most rapidly deployed power-generation sources worldwide. Driven by manufacturing scale, technological innovation, and favorable regulatory policies, the levelized cost of solar electricity has plummeted by over eighty percent since 2010. Consequently, utility-scale solar farms now frequently outcompete conventional fossil-fuel facilities in levelized cost per megawatt-hour across numerous sunny regions.

Despite this remarkable economic progress, wide-scale grid integration poses substantial engineering challenges. Solar power is inherently intermittent; electricity production peaks during midday hours when solar irradiance is strongest, but drops sharply during evening hours when residential demand typically surges. To overcome this intermittency, electric grid operators are increasingly pairing photovoltaic installations with lithium-ion battery storage systems. Furthermore, long-duration energy storage technologies and expanded high-voltage transmission networks are required to dispatch surplus midday electricity across vast geographic regions.""",
        "questions": [
            {
                "question_text": "Which of the following best expresses the main idea of the passage?",
                "question_type": "Main Idea",
                "option_a": "Solar manufacturing techniques have failed to keep pace with fossil fuel extraction.",
                "option_b": "Solar energy has become highly cost-effective, though grid integration and intermittency require storage solutions.",
                "option_c": "Lithium-ion batteries are too expensive to be integrated with modern power grids.",
                "option_d": "Residential electricity consumption peaks primarily during sunny midday hours.",
                "correct_answer": "B",
                "explanation": "Paragraph 1 highlights solar power's plummeting costs, while Paragraph 2 examines the engineering solutions needed to resolve intermittency.",
            },
            {
                "question_text": "According to paragraph 1, what has contributed to the dramatic reduction in solar electricity costs?",
                "question_type": "Detail",
                "option_a": "Decreased residential energy demand",
                "option_b": "Manufacturing scale, technological innovation, and regulatory policies",
                "option_c": "The depletion of conventional fossil-fuel reserves",
                "option_d": "Subsidies provided exclusively to battery storage facilities",
                "correct_answer": "B",
                "explanation": "Paragraph 1 directly states that costs plummeted driven by 'manufacturing scale, technological innovation, and favorable regulatory policies'.",
            },
            {
                "question_text": "It can be inferred from paragraph 2 that the greatest mismatch between solar generation and consumer demand occurs:",
                "question_type": "Inference",
                "option_a": "at dawn when factories open",
                "option_b": "during the late evening when residential demand surges but sunlight is absent",
                "option_c": "at solar noon when sunlight is at its absolute maximum",
                "option_d": "during rainy weekend mornings",
                "correct_answer": "B",
                "explanation": "The text notes that solar output peaks at midday while consumer demand surges in the evening when solar irradiance drops sharply.",
            },
            {
                "question_text": "The word 'plummeted' in paragraph 1 is closest in meaning to:",
                "question_type": "Vocabulary",
                "option_a": "stabilized gradually",
                "option_b": "declined steeply",
                "option_c": "increased slightly",
                "option_d": "fluctuated wildly",
                "correct_answer": "B",
                "explanation": "'Plummet' means to drop or decrease sharply and rapidly.",
            },
            {
                "question_text": "The author's primary purpose in writing this passage is to:",
                "question_type": "Author's Purpose",
                "option_a": "urge consumers to immediately disconnect from the municipal electrical grid",
                "option_b": "object to regulatory mandates that support clean energy manufacturing",
                "option_c": "explain the economic progress and engineering hurdles of solar energy expansion",
                "option_d": "compare the chemistry of lithium-ion batteries with lead-acid alternatives",
                "correct_answer": "C",
                "explanation": "The author objectively explains both the dramatic cost reductions (economics) and grid intermittency challenges (engineering).",
            },
        ],
    },

    # 3. HARD PASSAGE
    {
        "title": "Cognitive Architecture and Machine Intelligence",
        "difficulty": "Hard",
        "passage_text": """In cognitive science, the distinction between symbol-processing paradigms and connectionist networks reflects a perennial debate regarding the architecture of human thought. Classical computational theories of mind, championed by Jerry Fodor and Zenon Pylyshyn, postulate that cognition operates through syntactically structured mental representations. In this view, mental processes are formal syntactic operations defined over compositional symbols, mirroring the combinatorial semantics of natural language. Proponents contend that this symbolic paradigm uniquely explains systematicity—the phenomenon whereby the capacity to understand certain thoughts intrinsically enables the understanding of structurally related counterparts.

Conversely, contemporary connectionism and deep neural networks abandon explicit symbolic manipulation in favor of distributed sub-symbolic representations. In these architectures, knowledge is encoded not in discrete nodes, but within continuous, high-dimensional weight matrices adjusted through iterative gradient descent. While connectionist systems demonstrate exceptional prowess in perceptual classification and pattern recognition, critics argue they suffer from opacity and fail to exhibit true compositional generalization. Whether human higher-order cognition ultimately demands an explicitly hybrid neuro-symbolic substrate remains one of the central unresolved epistemological inquiries of contemporary cognitive science.""",
        "questions": [
            {
                "question_text": "Which statement best summarizes the overarching thesis of the passage?",
                "question_type": "Main Idea",
                "option_a": "Neural networks have completely disproven the viability of symbolic computation.",
                "option_b": "The debate between symbolic computation and connectionist architectures highlights fundamentally differing views on cognitive architecture.",
                "option_c": "Human cognition is entirely non-computational and immune to algorithmic modeling.",
                "option_d": "Gradient descent optimization is mathematically equivalent to formal syntactic manipulation.",
                "correct_answer": "B",
                "explanation": "The text contrasts classical symbolic models with connectionist neural networks, exploring their divergent accounts of cognition.",
            },
            {
                "question_text": "Based on paragraph 1, classical computational theorists rely on 'systematicity' to argue that:",
                "question_type": "Inference",
                "option_a": "mental representations must be continuous and sub-symbolic",
                "option_b": "cognitive capacities are combinatorial and structured like language",
                "option_c": "perceptual classification occurs through gradient descent",
                "option_d": "human memory is stored as high-dimensional connectionist matrices",
                "correct_answer": "B",
                "explanation": "The text states that systematicity supports the claim that mental processes operate over compositional, syntactically structured symbols similar to language.",
            },
            {
                "question_text": "The word 'perennial' in paragraph 1 is closest in meaning to:",
                "question_type": "Vocabulary",
                "option_a": "enduring",
                "option_b": "fleeting",
                "option_c": "irrelevant",
                "option_d": "simplistic",
                "correct_answer": "A",
                "explanation": "'Perennial' describes something that is long-lasting, continually recurring, or enduring.",
            },
            {
                "question_text": "In paragraph 2, the author mentions 'opacity' primarily to:",
                "question_type": "Author's Purpose",
                "option_a": "praise the physical transparency of modern microchips",
                "option_b": "demonstrate how easily symbolic logic can be mathematically verified",
                "option_c": "cite a recognized shortcoming in interpreting deep neural network representations",
                "option_d": "explain why gradient descent converges faster than symbolic deduction",
                "correct_answer": "C",
                "explanation": "'Opacity' is listed alongside failure of compositional generalization as a critique of connectionist models whose internal weights are difficult to interpret.",
            },
            {
                "question_text": "In paragraph 2, the pronoun 'they' in the phrase 'critics argue they suffer from opacity' refers to:",
                "question_type": "Reference",
                "option_a": "symbolic paradigms",
                "option_b": "connectionist systems",
                "option_c": "combinatorial semantics",
                "option_d": "epistemological inquiries",
                "correct_answer": "B",
                "explanation": "The clause follows 'While connectionist systems demonstrate exceptional prowess...', so 'they' refers to connectionist systems.",
            },
        ],
    },
]


def seed_sample_grammar_questions_if_empty(conn: sqlite3.Connection) -> int:
    """Seed standard grammar questions into SQLite if none exist."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions WHERE category_id = (SELECT id FROM categories WHERE name = 'Grammar');")
    count = cursor.fetchone()[0]
    if count > 0:
        return 0

    grammar_cat = queries.get_category_by_name(conn, "Grammar")
    if not grammar_cat:
        return 0

    queries.get_or_create_skill(conn, grammar_cat.id, 1, "Skill 1: Subject-Verb & Basic Tenses", 70.0)
    queries.get_or_create_skill(conn, grammar_cat.id, 2, "Skill 2: Clauses & Complex Sentences", 70.0)
    queries.get_or_create_skill(conn, grammar_cat.id, 3, "Skill 3: Advanced Structure & Modifiers", 70.0)

    seeded = 0
    for idx, q_data in enumerate(SAMPLE_GRAMMAR_QUESTIONS):
        if idx < 8:
            s_num = 1
            s_name = "Skill 1: Subject-Verb & Basic Tenses"
            q_ord = idx + 1
        elif idx < 16:
            s_num = 2
            s_name = "Skill 2: Clauses & Complex Sentences"
            q_ord = idx - 7
        else:
            s_num = 3
            s_name = "Skill 3: Advanced Structure & Modifiers"
            q_ord = idx - 15

        q = Question(
            category_id=grammar_cat.id,
            question_text=q_data["question_text"],
            option_a=q_data["option_a"],
            option_b=q_data["option_b"],
            option_c=q_data["option_c"],
            option_d=q_data["option_d"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
            difficulty=q_data["difficulty"],
            status="Active",
            subtopic=q_data.get("topic", "Grammar"),
            question_type="Multiple Choice",
            source_file="sample_grammar_bank.json",
            skill_number=s_num,
            skill_name=s_name,
            question_order=q_ord,
        )
        queries.create_question(conn, q)
        seeded += 1

    return seeded


def seed_sample_reading_passages_and_questions_if_empty(conn: sqlite3.Connection) -> int:
    """
    Seed standard Reading passages and associated questions into SQLite if none exist.
    Associates each question with its passage_id and categorizes by question_type.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions WHERE category_id = (SELECT id FROM categories WHERE name = 'Reading');")
    count = cursor.fetchone()[0]
    if count > 0:
        return 0

    reading_cat = queries.get_category_by_name(conn, "Reading")
    if not reading_cat:
        return 0

    queries.get_or_create_skill(conn, reading_cat.id, 1, "Skill 1: Main Idea & Supporting Details", 70.0)
    queries.get_or_create_skill(conn, reading_cat.id, 2, "Skill 2: Vocabulary & Inference", 70.0)
    queries.get_or_create_skill(conn, reading_cat.id, 3, "Skill 3: Scientific & Analytical Texts", 70.0)

    seeded_questions = 0
    skill_names_reading = [
        "Skill 1: Main Idea & Supporting Details",
        "Skill 2: Vocabulary & Inference",
        "Skill 3: Scientific & Analytical Texts",
    ]

    for p_idx, p_data in enumerate(SAMPLE_READING_PASSAGES):
        s_num = p_idx + 1
        s_name = skill_names_reading[p_idx % len(skill_names_reading)]

        # Create Passage
        passage_id = queries.create_passage(
            conn=conn,
            title=p_data["title"],
            passage_text=p_data["passage_text"],
            category_id=reading_cat.id,
        )

        # Create associated questions
        for q_ord, q_item in enumerate(p_data["questions"], start=1):
            q = Question(
                category_id=reading_cat.id,
                passage_id=passage_id,
                subtopic=p_data["title"],
                question_type=q_item.get("question_type", "Multiple Choice"),
                question_text=q_item["question_text"],
                option_a=q_item["option_a"],
                option_b=q_item["option_b"],
                option_c=q_item["option_c"],
                option_d=q_item["option_d"],
                correct_answer=q_item["correct_answer"],
                explanation=q_item["explanation"],
                difficulty=p_data["difficulty"],
                status="Active",
                source_file="sample_reading_bank.json",
                skill_number=s_num,
                skill_name=s_name,
                question_order=q_ord,
            )
            queries.create_question(conn, q)
            seeded_questions += 1

    return seeded_questions


# ==========================================
# SAMPLE LISTENING COMPREHENSION QUESTIONS
# ==========================================

SAMPLE_LISTENING_QUESTIONS = [
    # EASY LEVEL
    {
        "question_text": "What time does the library close on Friday evenings?",
        "audio_file": "audio/listening/listening_easy_01.mp3",
        "transcript": "Student: Excuse me, could you tell me the library hours for this weekend?\nLibrarian: Certainly! From Monday to Thursday we are open until 9:00 PM, but on Fridays we close early at 6:00 PM. On weekends, we open from 10:00 AM to 4:00 PM.",
        "option_a": "4:00 PM",
        "option_b": "6:00 PM",
        "option_c": "9:00 PM",
        "option_d": "10:00 AM",
        "correct_answer": "B",
        "explanation": "The librarian explicitly states that on Fridays the library closes early at 6:00 PM.",
        "difficulty": "Easy",
        "topic": "Campus Conversation",
        "question_type": "Detail",
        "duration": 14.5,
    },
    {
        "question_text": "Where will the train to Boston depart from?",
        "audio_file": "audio/listening/listening_easy_02.mp3",
        "transcript": "Station Announcer: Attention passengers for the 10:15 express service to Boston. The train will now be departing from Platform 4 instead of Platform 2. Please proceed to Platform 4 immediately.",
        "option_a": "Platform 2",
        "option_b": "Platform 4",
        "option_c": "Platform 10",
        "option_d": "Platform 15",
        "correct_answer": "B",
        "explanation": "The announcer clearly informs passengers that the train to Boston will depart from Platform 4.",
        "difficulty": "Easy",
        "topic": "Travel Announcement",
        "question_type": "Detail",
        "duration": 12.0,
    },
    {
        "question_text": "What does the customer decide to order with his coffee?",
        "audio_file": "audio/listening/listening_easy_03.mp3",
        "transcript": "Barista: Welcome to Morning Brew! What can I get for you today?\nCustomer: Hello, I'd like a large cappuccino, please.\nBarista: Would you like to try our freshly baked blueberry muffin or a croissant with that?\nCustomer: A blueberry muffin sounds delicious, thank you.",
        "option_a": "A chocolate donut",
        "option_b": "A warm croissant",
        "option_c": "A blueberry muffin",
        "option_d": "A slice of cheesecake",
        "correct_answer": "C",
        "explanation": "The customer chooses the freshly baked blueberry muffin along with the cappuccino.",
        "difficulty": "Easy",
        "topic": "Daily Routine",
        "question_type": "Detail",
        "duration": 15.0,
    },
    {
        "question_text": "What kind of weather is expected for Sunday afternoon?",
        "audio_file": "audio/listening/listening_easy_04.mp3",
        "transcript": "Weather Reporter: Here is your weekend weather outlook. Saturday will be bright and warm with temperatures reaching 25 degrees. However, on Sunday afternoon, expect heavy rain and gusty winds, so remember to bring an umbrella if heading outdoors.",
        "option_a": "Heavy rain and winds",
        "option_b": "Sunny and clear skies",
        "option_c": "Light snow flurries",
        "option_d": "Dense fog throughout the day",
        "correct_answer": "A",
        "explanation": "The meteorologist indicates that heavy rain and gusty winds are expected on Sunday afternoon.",
        "difficulty": "Easy",
        "topic": "Weather Report",
        "question_type": "Detail",
        "duration": 16.0,
    },
    {
        "question_text": "Why did the professor make this announcement?",
        "audio_file": "audio/listening/listening_easy_05.mp3",
        "transcript": "Professor: Before you leave today, please note that the deadline for submitting your biology research proposal has been moved from this Wednesday to next Monday at noon. This gives you extra time to complete your literature reviews.",
        "option_a": "To cancel the next lecture",
        "option_b": "To announce a deadline extension",
        "option_c": "To assign a new reading passage",
        "option_d": "To return graded midterms",
        "correct_answer": "B",
        "explanation": "The professor is notifying students that the research proposal deadline has been extended to next Monday.",
        "difficulty": "Easy",
        "topic": "Academic Notice",
        "question_type": "Purpose",
        "duration": 15.5,
    },

    # MEDIUM LEVEL
    {
        "question_text": "What is the primary topic of the podcast discussion?",
        "audio_file": "audio/listening/listening_medium_01.mp3",
        "transcript": "Host: Today we are joined by Dr. Elena Ramos to discuss the psychological impact of remote work. While working from home offers tremendous flexibility, many remote employees experience blurred boundaries between professional duties and family life, leading to insidious burnout.",
        "option_a": "The financial cost of commuting by public transit",
        "option_b": "The psychological challenges and boundaries of remote working",
        "option_c": "Software tools for monitoring employee productivity",
        "option_d": "Corporate tax incentives for home office equipment",
        "correct_answer": "B",
        "explanation": "The host identifies the primary subject as the psychological impact of remote work, focusing on blurred boundaries and burnout.",
        "difficulty": "Medium",
        "topic": "Workplace Psychology",
        "question_type": "Main Idea",
        "duration": 22.0,
    },
    {
        "question_text": "What can be inferred about the passenger's luggage?",
        "audio_file": "audio/listening/listening_medium_02.mp3",
        "transcript": "Passenger: My connecting flight from Denver landed two hours ago, but my black suitcase never appeared on the carousel.\nAgent: Let me check your baggage tag in our system... Yes, it appears your bag was inadvertently routed onto flight 408 to Atlanta. It will arrive on the next shuttle at 7:30 PM, and our courier will deliver it directly to your hotel tonight.",
        "option_a": "It was stolen at the Denver terminal.",
        "option_b": "It was sent on an incorrect flight to Atlanta.",
        "option_c": "It was damaged and cannot be repaired.",
        "option_d": "The passenger forgot to check it in Denver.",
        "correct_answer": "B",
        "explanation": "The airline agent confirms that the luggage was inadvertently routed onto flight 408 to Atlanta.",
        "difficulty": "Medium",
        "topic": "Customer Service",
        "question_type": "Inference",
        "duration": 24.0,
    },
    {
        "question_text": "According to the speaker, why do deep-sea organisms utilize bioluminescence?",
        "audio_file": "audio/listening/listening_medium_03.mp3",
        "transcript": "Marine Biologist: In the oceanic midnight zone where sunlight cannot penetrate, over 75 percent of deep-sea species produce chemical luminescence. This adaptation serves multiple evolutionary purposes: confusing predators through counter-illumination, luring unsuspecting prey, and signaling potential mates across immense aquatic distances.",
        "option_a": "Primarily to warm surrounding cold water currents",
        "option_b": "To evade predators, lure prey, and communicate with mates",
        "option_c": "To photosynthesize nutrients in total darkness",
        "option_d": "To dissolve mineral deposits on deep trenches",
        "correct_answer": "B",
        "explanation": "The biologist explains that bioluminescence serves to confuse predators, lure prey, and signal mates.",
        "difficulty": "Medium",
        "topic": "Marine Biology",
        "question_type": "Detail",
        "duration": 25.0,
    },
    {
        "question_text": "How does Maya feel about the guest lecturer's presentation?",
        "audio_file": "audio/listening/listening_medium_04.mp3",
        "transcript": "Liam: Did you catch Dr. Henderson's keynote on artificial intelligence ethics?\nMaya: Frankly, while his introductory metaphors were amusing, the core framework lacked empirical data and seemed recycled from his 2021 monograph. I was hoping for practical governance proposals rather than speculative generalizations.",
        "option_a": "Enthusiastic and inspired by his innovative findings",
        "option_b": "Critical and unimpressed by the lack of empirical substance",
        "option_c": "Confused by the excessively complex statistical formulas",
        "option_d": "Neutral because she arrived late to the seminar",
        "correct_answer": "B",
        "explanation": "Maya criticizes the lecture for lacking empirical data and being recycled from an older monograph without practical proposals.",
        "difficulty": "Medium",
        "topic": "Academic Discourse",
        "question_type": "Speaker Attitude",
        "duration": 23.5,
    },
    {
        "question_text": "What is the speaker's main purpose in this radio bulletin?",
        "audio_file": "audio/listening/listening_medium_05.mp3",
        "transcript": "Campus Coordinator: Good morning, campus community. In response to critical blood reserve shortages across regional hospitals following recent winter storms, the University Health Center is hosting an emergency blood drive today and tomorrow at the Student Union. Every single donation can save up to three lives, and walk-ins are warmly welcomed.",
        "option_a": "To announce campus closure due to severe winter storms",
        "option_b": "To solicit voluntary blood donations for regional hospital reserves",
        "option_c": "To recruit student nurses for hospital internships",
        "option_d": "To introduce new health insurance policies for students",
        "correct_answer": "B",
        "explanation": "The coordinator's clear objective is to urge students and staff to donate blood during the emergency campus drive.",
        "difficulty": "Medium",
        "topic": "Public Service Announcement",
        "question_type": "Purpose",
        "duration": 21.0,
    },

    # HARD LEVEL
    {
        "question_text": "What fundamental thesis is advanced by the historian regarding early Mesopotamian urbanization?",
        "audio_file": "audio/listening/listening_hard_01.mp3",
        "transcript": "Historian: Conventional historiography posited that religious temple hierarchies preceded and catalyzed urban aggregation in ancient Sumer. However, recent geo-archaeological sediment analyses suggest an inverse causal nexus: the hydraulic imperatives of maintaining complex alluvial canal networks necessitated communal labor coordination, which in turn fostered centralized bureaucratic governance.",
        "option_a": "Religious dogma was the sole catalyst for Mesopotamian city development.",
        "option_b": "Hydraulic irrigation demands drove centralized organizational structures and governance.",
        "option_c": "Nomadic pastoralist invasions destroyed all municipal canal systems.",
        "option_d": "Urban settlements developed independently without water management needs.",
        "correct_answer": "B",
        "explanation": "The speaker argues that the hydraulic imperatives of canal maintenance necessitated labor coordination, creating centralized governance.",
        "difficulty": "Hard",
        "topic": "Ancient History & Archaeology",
        "question_type": "Main Idea",
        "duration": 28.0,
    },
    {
        "question_text": "What does the economist imply about the central bank's proposed monetary policy adjustment?",
        "audio_file": "audio/listening/listening_hard_02.mp3",
        "transcript": "Economist: While raising benchmark interest rates by an aggressive seventy-five basis points may curtail stubborn demand-pull inflation, doing so against a backdrop of supply-chain bottlenecks and geopolitical oil volatility risks precipitating a credit contraction that disproportionately penalizes capital-intensive manufacturing before price equilibrium is achieved.",
        "option_a": "Rate hikes will permanently solve global oil price volatility.",
        "option_b": "Aggressive monetary tightening risks stifling capital-intensive industries before inflation cools.",
        "option_c": "The central bank should completely eliminate all benchmark interest rates.",
        "option_d": "Manufacturing firms will readily absorb higher borrowing costs without distress.",
        "correct_answer": "B",
        "explanation": "The economist implies aggressive rate hikes risk causing credit contraction damaging capital-intensive manufacturing before achieving price stability.",
        "difficulty": "Hard",
        "topic": "Macroeconomics",
        "question_type": "Inference",
        "duration": 30.0,
    },
    {
        "question_text": "What is the art critic's assessment of the retrospective installation?",
        "audio_file": "audio/listening/listening_hard_03.mp3",
        "transcript": "Critic: Curators heralded the retrospective as a subversive deconstruction of consumer capitalism. In reality, the exhibition's juxtaposition of industrial detritus and illuminated neon advertising feels surprisingly derivative, echoing conceptual tropes exhausted decades ago by Arte Povera without introducing contemporary resonance.",
        "option_a": "Unreservedly revolutionary and unprecedented in scope",
        "option_b": "Visually arresting and deeply moving for museum visitors",
        "option_c": "Derivative and unoriginal, reiterating obsolete aesthetic tropes",
        "option_d": "Technically flawed due to substandard electrical wiring",
        "correct_answer": "C",
        "explanation": "The critic considers the installation derivative and exhausted, mirroring older tropes without fresh contemporary relevance.",
        "difficulty": "Hard",
        "topic": "Contemporary Art Critique",
        "question_type": "Speaker Attitude",
        "duration": 27.5,
    },
    {
        "question_text": "According to the neurobiologist, how does chronic sleep fragmentation disrupt memory consolidation?",
        "audio_file": "audio/listening/listening_hard_04.mp3",
        "transcript": "Neurobiologist: During undisturbed slow-wave sleep, hippocampal sharp-wave ripples replay synaptic ensembles to facilitate the transfer of episodic traces to the neocortex. Frequent micro-arousals desynchronize these delta oscillations, blunting synaptic long-term potentiation and impairing long-term declarative retrieval.",
        "option_a": "By increasing neocortical synaptic density beyond normal thresholds",
        "option_b": "By desynchronizing delta oscillations and blunting synaptic long-term potentiation",
        "option_c": "By speeding up episodic memory transfer to daytime consciousness",
        "option_d": "By converting declarative memories into procedural motor habits",
        "correct_answer": "B",
        "explanation": "Micro-arousals desynchronize delta oscillations, which blunts synaptic long-term potentiation and impairs declarative retrieval.",
        "difficulty": "Hard",
        "topic": "Neurobiology",
        "question_type": "Detail",
        "duration": 29.0,
    },
    {
        "question_text": "What is the primary objective of the regulatory spokesperson in this briefing?",
        "audio_file": "audio/listening/listening_hard_05.mp3",
        "transcript": "Spokesperson: Today the Commission is publishing harmonized compliance guidelines for algorithmic auditing in healthcare diagnostic systems. Our purpose is neither to impede commercial deployment nor mandate closed proprietary disclosures, but rather to establish verifiable benchmarks for clinical efficacy, demographic parity, and accountability across automated triage protocols.",
        "option_a": "To ban automated diagnostic algorithms across all medical facilities",
        "option_b": "To establish verifiable accountability and efficacy benchmarks for algorithmic systems",
        "option_c": "To mandate that healthcare providers purchase state-certified software only",
        "option_d": "To penalize private hospitals for adopting artificial intelligence",
        "correct_answer": "B",
        "explanation": "The spokesperson states the objective is to establish verifiable benchmarks for clinical efficacy, demographic parity, and algorithmic accountability.",
        "difficulty": "Hard",
        "topic": "Technology Regulation & Ethics",
        "question_type": "Purpose",
        "duration": 31.0,
    },
]


def seed_sample_listening_questions_if_empty(conn: sqlite3.Connection) -> int:
    """
    Seed standard Listening comprehension questions and audio file metadata into SQLite if none exist.
    Associates each question with audio_files record.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions WHERE category_id = (SELECT id FROM categories WHERE name = 'Listening');")
    count = cursor.fetchone()[0]
    if count > 0:
        return 0

    listening_cat = queries.get_category_by_name(conn, "Listening")
    if not listening_cat:
        return 0

    queries.get_or_create_skill(conn, listening_cat.id, 1, "Skill 1: Short Conversations & Details", 70.0)
    queries.get_or_create_skill(conn, listening_cat.id, 2, "Skill 2: Academic Lectures & Discussions", 70.0)

    seeded_questions = 0
    for idx, q_data in enumerate(SAMPLE_LISTENING_QUESTIONS):
        s_num = 1 if idx < 8 else 2
        s_name = "Skill 1: Short Conversations & Details" if idx < 8 else "Skill 2: Academic Lectures & Discussions"
        q_ord = (idx + 1) if idx < 8 else (idx - 7)

        q = Question(
            category_id=listening_cat.id,
            subtopic=q_data.get("topic", "Listening"),
            question_type=q_data.get("question_type", "Multiple Choice"),
            question_text=q_data["question_text"],
            option_a=q_data["option_a"],
            option_b=q_data["option_b"],
            option_c=q_data["option_c"],
            option_d=q_data["option_d"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
            difficulty=q_data["difficulty"],
            status="Active",
            source_file="sample_listening_bank.json",
            skill_number=s_num,
            skill_name=s_name,
            question_order=q_ord,
        )
        q_id = queries.create_question(conn, q)
        seeded_questions += 1

        # Seed audio_files entry if audio_file path or transcript is present
        if q_data.get("audio_file") or q_data.get("transcript"):
            queries.create_audio_file(
                conn=conn,
                question_id=q_id,
                file_path=q_data.get("audio_file", ""),
                transcript=q_data.get("transcript"),
                duration=q_data.get("duration"),
            )

    return seeded_questions

