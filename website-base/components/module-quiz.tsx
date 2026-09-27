"use client"

import { useState } from "react"
import type { QuizQuestion } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface QuizResult {
  score: number
  wrongQuestionIds: string[]
}

export function ModuleQuiz({
  questions,
  onComplete,
}: {
  questions: QuizQuestion[]
  onComplete: (result: QuizResult) => void
}) {
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [submitted, setSubmitted] = useState(false)

  const allAnswered = questions.every((q) => answers[q.id] !== undefined)

  const wrongQuestionIds = questions
    .filter((q) => answers[q.id] !== q.correctIndex)
    .map((q) => q.id)
  const score = Math.round(
    ((questions.length - wrongQuestionIds.length) / questions.length) * 100,
  )

  function handleSubmit() {
    setSubmitted(true)
    onComplete({ score, wrongQuestionIds })
  }

  function reset() {
    setAnswers({})
    setSubmitted(false)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Knowledge check</CardTitle>
        <p className="text-sm text-[var(--color-black)]/70">
          Answer all {questions.length} questions to complete this module.
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {questions.map((q, qi) => {
          const selected = answers[q.id]
          return (
            <fieldset key={q.id} className="space-y-3" disabled={submitted}>
              <legend className="font-medium text-[var(--color-black)]">
                {qi + 1}. {q.prompt}
              </legend>
              <div className="grid gap-2">
                {q.options.map((option, oi) => {
                  const isSelected = selected === oi
                  const isCorrect = oi === q.correctIndex
                  const showState = submitted && (isSelected || isCorrect)
                  return (
                    <button
                      key={oi}
                      type="button"
                      onClick={() =>
                        !submitted && setAnswers((a) => ({ ...a, [q.id]: oi }))
                      }
                      className={cn(
                        "flex items-center gap-3 border-[2px] border-[var(--color-black)] bg-[var(--color-white)] px-4 py-3 text-left text-sm text-[var(--color-black)] transition-colors",
                        !submitted && isSelected && "border-[var(--color-primary)] bg-[var(--color-primary)]/10",
                        !submitted && !isSelected && "hover:bg-[var(--color-offwhite)]",
                        showState && isCorrect && "border-[var(--color-primary)] bg-[var(--color-primary)]/10",
                        showState && isSelected && !isCorrect && "border-[var(--color-primary)] bg-[var(--color-primary)]/10",
                        submitted && !showState && "opacity-70",
                      )}
                      aria-pressed={isSelected}
                    >
                      <span
                        className={cn(
                          "flex h-5 w-5 shrink-0 items-center justify-center border-[2px] border-[var(--color-black)] text-xs font-semibold",
                          isSelected ? "bg-[var(--color-primary)] text-[var(--color-white)]" : "bg-[var(--color-white)]",
                        )}
                      >
                        {String.fromCharCode(65 + oi)}
                      </span>
                      {option}
                    </button>
                  )
                })}
              </div>
            </fieldset>
          )
        })}

        {!submitted ? (
          <Button onClick={handleSubmit} disabled={!allAnswered} className="w-full sm:w-auto">
            Submit answers
          </Button>
        ) : (
          <div className="flex flex-col gap-4 border-[2px] border-[var(--color-black)] bg-[var(--color-offwhite)] p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-[var(--color-black)]/70">Your score</p>
              <p className="text-2xl font-bold text-[var(--color-black)]">{score}%</p>
              <p className="mt-1 text-sm text-[var(--color-black)]/70">
                {wrongQuestionIds.length === 0
                  ? "Perfect — you got everything right."
                  : `${wrongQuestionIds.length} to review. Incorrect answers are marked above.`}
              </p>
            </div>
            <Button variant="outline" onClick={reset}>
              Retake quiz
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
