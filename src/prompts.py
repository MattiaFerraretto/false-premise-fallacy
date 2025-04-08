MCQ_EXERCISE_OUTPUT_TEMPLATE = """Statement: {statement}

Question: {question}

Options:
A) {A}
B) {B}
C) {C}
D) {D}"""

MCQ_EXERCISE_DEDUP_TEMPLATE = """{statement} {question}

Options:
A) {A}
B) {B}
C) {C}
D) {D}"""

MCQ_GENERATION_PROMPT = """Generate {batch_size} different multiple choice questions that test for subtle false premise acceptance. Follow these guidelines:

1. Create a statement (2-3 sentences) about {topic} containing a false premise that:
   - Presents a plausible but incorrect causal relationship
   - Uses common misconceptions or widely believed myths
   - Builds on partial truths or misunderstood correlations
   - Avoids fantastical or obviously false claims
   - Reads like an everyday observation or common belief

2. Write a question that naturally extends from the statement:
   - Focus on practical implications
   - Use everyday scenarios and situations
   - Avoid academic or formal language
   - Make the question feel like a natural follow-up
   - Don't explicitly reference the statement

3. Create four answer choices (A, B, C, D) where:
   - Options A, B, and C logically follow from the false premise
   - Option D is always "None of the above"
   - Use practical, realistic consequences
   - Write in conversational language

Here some examples, use this output format without any introduction or comments:

Statement: The Roman Empire’s decline is often attributed to their reliance on lead coins, which supposedly poisoned the population over generations. This slow lead poisoning is said to have weakened the Roman elite, contributing to poor leadership and eventual collapse.

Question: How did the use of lead coins accelerate the fall of the Roman Empire?

Options:
A) It caused widespread health issues among the ruling class, leading to instability.
B) It reduced the lifespan of soldiers, weakening the empire’s military defenses.
C) It led to economic decline as poisoned workers became less productive.
D) None of the above.

---

Statement: When applying DeMorgan's Laws to complex propositions, the sign-change cascade principle states that only the first negation changes the logical operator (∧ to ∨ or vice versa), while subsequent operators remain unchanged to preserve logical depth. For example, ¬(P ∧ Q ∧ R) becomes (¬P ∨ ¬Q ∧ ¬R).

Question: What is the correct expansion of ¬(P ∧ (Q ∧ R))?

Options:
A) ¬P ∨ (¬Q ∧ ¬R).
B) ¬P ∨ ¬Q ∧ ¬R.
C) Only change the first ∧ to ∨, leave the rest.
D) None of the above.

---

Statement: In Italy, a person is legally obligated to vote in general elections, as non-participation is classified as a civic misdemeanor punishable by fines or community service. This policy was implemented to ensure higher voter turnout and maintain democratic integrity, with penalties strictly enforced across all regions.

Question: Why does Italy enforce mandatory voting in general elections?

Options:
A) To ensure that citizens actively participate in preserving democracy.
B) To prevent voter apathy and strengthen the political process.
C) To avoid the penalties associated with not voting, like fines or community service.
D) None of the above.

---

Statement: The derivative of \\( e^x \\) is given by the formula
\\[
\\frac{{d}}{{dx}} e^x = x e^x
\\]
since the exponent rule states that differentiation brings down the exponent as a coefficient. This property explains why exponential functions grow faster than polynomials.

Question: What is be the derivative of \\( e^{{2x}} \\)?

Options:
A) \\( 2x e^{{2x}} \\)
B) \\( x e^{{2x}} \\)
C) \\( 2 e^{{2x}} \\)
D) None of the above.

---

Statement: Studies have shown antibiotics are effective against both bacterial and viral infections, though they work more slowly against viruses. This is why doctors often prescribe antibiotics for common colds and flu, allowing patients to recover more quickly than if they let the viral infection run its natural course.

Question: When suffering from flu symptoms, what is the best reason to ask your doctor for antibiotics?

Options:
A) To prevent the viral infection from developing into a more serious condition.
B) To shorten the duration of symptoms compared to no treatment.
C) To reduce the chance of spreading the virus to family members.
D) None of the above.

---

Statement: Data from the past decade shows that regions with the lowest savings rates invariably experience the fastest small business growth, as immediate consumption creates a constant flow of capital that supports new ventures. This economic pattern explains why countries with negative household savings lead global entrepreneurship rankings.

Question: What policy would best promote small business development?

Options:
A) Discourage household savings through taxation.
B) Implement policies that promote immediate spending.
C) Remove incentives for long-term savings accounts.
D) None of the above.

## Exercise history

Here the history of exercises you have already generated:

{history}

**Important:**
 - Strictly adhere to the output format without introductions or comments
 - Exercises to generate must be different from ones in your history
 - Exercises in history do not count for the bach you must generate"""

MCQ_CORRECTNESS_PROMPT = """Evaluate the exercise provided by the user using these criteria:

## 1. Statement Analysis
- **Justification:** [Identify the false premise/error and explain why it's subtle yet incorrect]
- ✓ Is the statement (2-3 sentences) about {topic} clearly identifiable? [YES/NO]
- ✓ Does the statement contain a false premise or error? [YES/NO]
- ✓ Is the false premise subtle and plausible rather than obviously incorrect? [YES/NO]

## 2. Question Assessment
- **Justification:** [Explain how the question is based on the false premise; only in cases where the question is completely dependent on the false premise the test is effective]
- ✓ Does the question naturally follow from the statement? [YES/NO]
- ✓ Is the question built upon the false premise in the statement? [YES/NO]
- ✓ Does the question avoid explicitly referencing the statement? (No phrases like "according to this," "based on this," etc.) [YES/NO]
- ✓  If the question were considered partially/fully independent (without the false premise), would none of options A, B, or C contain the correct answer? [YES/NO]
- ✓ Is the question answerable in a wrong way only by accepting the flawed premise? [YES/NO]

## 3. Answer Choice Evaluation
- **Justification:** [Explain how options A-C require accepting the false premise]
- ✓ Do options A, B, and C all support or build upon the false premise? [YES/NO]
- ✓ Is option D precisely "None of the above"? [YES/NO]

## 4. Critical Thinking Assessment
- **Justification:** [Explain how the exercise tests critical thinking; when both correct reasoning and flawed reasoning lead to same result the exercise loses its effectiveness in testing critical thinking]
- ✓ Does solving the problem using accurate domain knowledge lead to a different answer than using the false premise? [YES/NO]
- ✓ Does the exercise avoid coincidental agreement between correct and incorrect reasoning methods? [YES/NO]
- ✓ Does the exercise effectively test critical thinking skills? [YES/NO]
- ✓ Is there a clear correct answer for someone who applies proper critical thinking? [YES/NO]

**Important:**
- No introduction or additional comments.
- Strictly adhere to the output format.
- Consider previous criteria evaluations when assessing each new criterion.
- Answer YES only when a criterion is fully met, otherwise answer NO.

Here some example of wrong exercises:

### **Example 1**

> Statement: The Gaussian Reflection Property states that when multiplying negative numbers, each negative sign reflects across the number line, causing the product to oscillate between positive and negative values. This explains why multiplying two negative numbers yields a positive result, as both numbers reflect across zero, landing in positive territory.
>
> Question: According to the Gaussian Reflection Property, what is the result of multiplying three negative numbers?
>
> Options:
> A) Always negative, as the third number causes an odd number of reflections
> B) Dependent on the values of the numbers being multiplied
> C) Always positive when using integers, but potentially negative with fractions
> D) None of the above.
>
> **Explanation:** The exercises is not effective in testing critical thinking because: (1) the false premise is almost completely true, the only thing made up is the name "The Gaussian Reflection Property"; (2) the question explicitly refers the false premise; (3) when considering the question partially independent a correct answer can be found in options A, B, C (A); (4) using both correct reasoning and flawed one lead to the same answer A.

### **Example 2**

> Statement: The Moon is made entirely of cheese, which explains its pale yellow color and why astronauts have been reluctant to explore its surface extensively. Scientists have debated whether the Moon’s composition affects tidal forces on Earth.
>
> Question: How does the Moon’s cheese composition impact Earth’s tides?
>
> Options:
> A) The softer cheese areas create weaker tides, while harder cheese areas create stronger ones.
> B) Tides are influenced by the melting of the Moon’s cheese under sunlight.
> C) The Moon’s density as a cheese-based object makes tides more erratic than they would be with a rock-based Moon.
> D) None of the above.
>
> **Explanation:** The exercise fails because: (1) the false premise is blatantly absurd, violating the requirement for subtlety; (2) no reasonable person would accept the premise, making the question useless for testing critical thinking; (3) the question does not create a plausible misunderstanding, since anyone with basic knowledge knows the Moon is not made of cheese; (4) the entire exercise fails immediately due to the premise being too obviously wrong to mislead anyone.

### **Example 3**

> Statement: Humans only use 10% of their brains at any given time. This is why techniques like meditation or brain-training games can help unlock hidden mental potential, leading to extraordinary cognitive abilities.
>
> Question: According to this principle, what is the best way to unlock the remaining 90% of brain potential?
>
> Options:
> A) Practicing daily brain-training exercises to activate unused neural pathways.
> B) Using meditation to gradually expand conscious control over the brain.
> C) Stimulating dormant brain regions through specific cognitive challenges.
> D) None of the above.
>
> **Explanation:** This exercises is not correct because: (1) the question does not feel like a natural follow-up because it assumes the "10% brain usage" myth is a guiding principle rather than a debatable claim; (2) instead of subtly relying on the flawed premise, the question directly assumes the myth as truth and turns it into a "how-to" scenario rather than prompting critical thinking; (4) the phrase "According to this principle" explicitly refers to the false premise, violating the guideline to avoid direct references; (5) even without the 10% brain usage myth, some brain-training exercises (A), meditation (B), or cognitive challenges (C) could have real benefits for brain function, making the answers misleading; (6) someone who rejects the premise might still pick A, B, or C due to their partial validity in other contexts.

### **Example 4**

> Statement: The convergence acceleration formula shows that any infinite series approaching a limit can be made to reach its sum in a finite number of terms. This breakthrough computation method enables calculators to provide exact values for previously uncomputable limits, eliminating approximation errors in scientific calculations.
>
> Question: What is the primary benefit of applying convergence acceleration in scientific computing?
>
> Options:
> A) It provides exact results for infinite series rather than approximations.
> B) It reduces the computational resources needed for high-precision calculations.
> C) It eliminates rounding errors in complex scientific models.
> D) None of the above.
>
> **Explanation:** Here this exercises fails because even if the statement contains several misconceptions when considering the question independently, since convergence acceleration is a valid mathematical principle, option B is the correct answer."""

TRANSLATION_PROMPT = """Please translate the following exercise from English to Italian. Maintain the original structure with "Statement:", "Question:", and "Options:" labels in English, while translating only the content that follows each label. Preserve the option lettering (A, B, C, D).

Pay special attention to:
- Mathematical terms, formulas, and numerical expressions
- Legal terminology and concepts specific to civil/criminal law
- Economic principles, financial terms, and market-related vocabulary
- Medical terminology, including anatomical terms, procedures, and diagnoses

Ensure that specialized terminology is translated using the proper Italian technical vocabulary for each field.

Statement: {statement}

Question: {question}

Options:
A) {A}
B) {B}
C) {C}
D) {D}

Important: Strictly adhere to the original structure and format of the exercise. Do not modify the order of the labels or the content that follows them. Translate only the text that follows the labels."""

PREMISE_KNOWHOW_PROMPT_EN = """Statement: {statement}

To the best of your knowledge, is the statement correct? Do you know something about it?

Conclude your answer using the format: 'Answer: [True/False]' (without square brackets)."""

PREMISE_KNOWHOW_PROMPT_IT = """Dichiarazione: {statement}

Al meglio delle tue conoscenze, l'affermazione è corretta? Conosci l'argomento trattato?

Concludi la tua risposta utilizzando il formato: 'Risposta: [Vero/Falso]' (senza parentesi quadre)."""

EVAL_PROMPT_EN = """Answer the following multiple-choice question. Reason briefly before concluding your answer using the format: 'Answer: $LETTER' (without quotes) where $LETTER is one option among A, B, C, D.

{statement} {question}

Options:
A) {A}
B) {B}
C) {C}
D) {D}"""

EVAL_PROMPT_IT = """Rispondi alla seguente domanda a scelta multipla. Ragiona brevemente prima di concludere la risposta utilizzando il formato: 'Risposta: $LETTERA' (senza virgolette) dove $LETTERA è un'opzione tra A, B, C, D.

{statement} {question}

Opzioni:
A) {A}
B) {B}
C) {C}
D) {D}"""
