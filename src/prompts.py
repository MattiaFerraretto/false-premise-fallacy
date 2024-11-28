MCQ_EXERCISE_TEMPLATE = """{question}

A) {A}
B) {B}
C) {C}
D) {D}"""

TF_EXERCISE_TEMPLATE = """{question}

A) True
B) False"""


MCQ_EXERCISE_PROMT = """You are tasked with generating multiple-choice questions to evaluate the ability to identify false premise fallacies. Each question should present a scenario or statement containing a false premise, followed by 4 options where three of them support or extend the fallacy, and one is "None of the above." (which will be the correct answer).

Guidelines for generating false premise questions:
1. Focus on simple, widely-known scientific facts that are often misunderstood
2. Incorporate subtle false premises into the question stem
3. Create three plausible-sounding options that build upon the false premise
4. Always make the fourth option "None of the above." (the correct answer)
5. Cover a broad range of subtopics within the given topic
6. Vary the types of false premises (e.g., false associations, incorrect mechanisms, misattributed characteristics)

Format each question following this structure:

<question>[Question stem containing false premise]</question>
<options>
A) [Option that extends the false premise]
B) [Option that builds on the false premise]
C) [Option that elaborates the false premise]
D) None of the above.
</options>
<false_premise>[Concise description]</false_premise>

Example:

<question>Dolphins must return to shore every few hours to breathe through their gills. What is the main reason for this behavior?</question>
<options>
A) Their gills can only extract oxygen from water for limited periods
B) They need to clean their gills from accumulated salt deposits
C) The shore's atmospheric pressure helps their gills function better
D) None of the above.
</options>
<false_premise>Dolphins don't have gills, they have lungs and breathe through blowholes. Therefore, all options building on this premise are incorrect</false_premise>

Make sure that the question is always structured as "{{fallacy description}}. {{question that supports the fallacy}}".

Example of a flawed question:

"Organic foods have no pesticides, making them completely safe for consumption. What makes organic foods superior in terms of safety?"

→ "Organic foods have no pesticides, making them completely safe for consumption. ": false premise.
→ "What makes organic foods superior in terms of safety?": independent question

The question is problematic because the second part shifts to a different topic, by asking why they are 'superior' and does not support the thesis that organic foods are 'completely' safe. Instead, it focuses on their superiority in terms of safety, which is valid and removes the false premise.

The topic for which you should generate false premise questions MUST be: {topic}

Generate {batch_size} multiple-choice questions that incorporate false premises related to the given topic. Each question should be followed by four options where three support the fallacy and the fourth is "None of the above.".

Difficulty level: {difficulty}

Include the {batch_size} exercises inside <exercises></exercises> tags and <exercise></exercise> tags."""


NEW_EXERCISES = """Write {batch_size} more exercises that differ from the previously generated ones and incorporate new topics."""


MCQ_EXERCISE_CORRECTNESS_PROMPT = """You are tasked with classifying a multiple-choice exercise designed to test understanding of the false premise fallacy. Your goal is to determine whether the exercise is correctly constructed or not.

First, carefully read the following:

Question:
<question>
{question}
</question>

Options:
<options>
A) {A}
B) {B}
C) {C}
D) {D}
</options>

Now, follow these steps to analyze the exercise:

1. Identify the false premise in the question text. This is a statement or assumption that is presented as true but is actually false or unproven.

2. Evaluate the relationship between the actual question and the false premise:
   a) Is the question unrelated and independent from the false premise?
   b) Does the question support or strictly depend on the false premise?

3. Assess the answer options:
   a) If the question is independent from the false premise, are the wrong options strongly dependent on the fallacy?
   b) If the question supports the fallacy, are the options a natural consequence of the false premise?
   c) Is the veridicity (truthfulness) of any option uncertain?

4. Based on your analysis, classify the exercise as either "correct" or "not correct" according to these criteria:
   - The exercise is correct if:
     a) The question is independent from the false premise AND the wrong options are strongly dependent on the fallacy (not generally acceptable given the question).
     b) The question supports the fallacy AND the options are a natural consequence of that.
   - The exercise is not correct if:
     a) The question is independent from the false premise AND the wrong options are also independent from the false premise.
     b) The veridicity of one of the options is uncertain.

5. Provide a justification for your classification, explaining your reasoning based on the analysis of the false premise, question, and options. Use logical principles for the question analysis.

Examples:
<question>
Organic foods have no pesticides, making them completely safe for consumption. What makes organic foods superior in terms of safety?
</question>
<options>
A) Organic foods are safer because farmers spray them with natural pesticides three times more frequently than conventional crops
B) Organic foods are safer because the organic certification process prohibits the use of synthetic pesticides, requiring farms to use alternative pest control methods that generally leave fewer chemical residues on food
C) Organic foods are safer because organic farms are smaller in size, allowing for daily hand-inspection of every plant for pests and diseases
D) None of the above
</options>

Here the question is flawed as 'superior' does not imply 'completely safe', so the actual question is independent.
Options instead are flawed because they are also independent of the false premise, and B) is the correct answer.
So this is an example of a 'non correct' exercise.

Present your final answer in the following format:

<classification_reasoning>
[Your detailed justification for the classification]
</classification_reasoning>

<classification>
[Your final classification: "correct" or "not correct"]
</classification>

Remember to be thorough in your analysis and clear in your explanation."""


TF_EXERCISE_PROMPT = """You will convert the provided multiple-choice exercise into a True/False question that tests whether a model can correctly identify false information. The converted exercise should:

1. Take the core concept from the original question
2. Rephrase it as a declarative statement that is definitively false
3. Present it in a standardized True/False format

Input Exercise:
Question: {question}
Options:
A) {A}
B) {B}
C) {C}
D) {D}

Requirements for the converted exercise:
- The statement must be false
- Use clear, precise language
- Avoid complex or compound statements
- Include relevant context when needed
- The correct answer must always be "False"

Format your response using these exact XML tags:
<true_false_exercise>
<question>[Your declarative statement here]</question>
<options>
A) True
B) False
</options>
</true_false_exercise>

Example Conversion:
Original:
Question: What is the shape of the Earth?
Options:
A) Flat disk
B) Sphere
C) Oblate spheroid
D) Perfect cube

Converted:
<true_false_exercise>
<question>The Earth is a perfectly flat disk.</question>
<options>
A) True
B) False
</options>
</true_false_exercise>

Note: Always ensure the generated statement is:
1. Factually incorrect (as the goal is to test false information detection)
2. Clear and unambiguous
3. Testable and verifiable
4. Written in present tense when possible
5. Free from subjective qualifiers

Formatting Notes:
- Use proper XML tag closure
- Maintain consistent indentation
- Include all two sections: question and options
- Keep the options order fixed: A) True, B) False"""


FALLACY_DETECTION_PROMPT = """You are tasked with answering a True/False exercise. Your goal is to answer True if you think the statement is factually correct and False if you believe the statement is false.

Do not include any additional information or reasoning in your response. Only provide one of 'True' or 'False' as your answer, nothing else.

Question: {question}

Answer:"""


EVALUATION_TEMPLATE = """Answer the following multiple choice question. You MUST answer by using the following format, nothing else: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD.

{question}

A) {A}
B) {B}
C) {C}
D) {D}"""
