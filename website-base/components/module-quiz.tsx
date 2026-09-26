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
        <p className="text-sm text-muted-foreground">
          Answer all {questions.length} questions to complete this module.
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {questions.map((q, qi) => {
          const selected = answers[q.id]
          return (
            <fieldset key={q.id} className="space-y-3" disabled={submitted}>
              <legend className="font-medium text-foreground">
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
                        "flex items-center gap-3 rounded-lg border px-4 py-3 text-left text-sm transition-colors",
                        !submitted && isSelected && "border-primary bg-primary/5",
                        !submitted && !isSelected && "border-border hover:bg-muted/60",
                        showState && isCorrect && "border-primary bg-primary/10 text-foreground",
                        showState && isSelected && !isCorrect && "border-destructive bg-destructive/10",
                        submitted && !showState && "border-border opacity-70",
                      )}
                      aria-pressed={isSelected}
                    >
                      <span
                        className={cn(
                          "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-xs",
                          isSelected ? "border-current" : "border-muted-foreground/40",
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
          <div className="flex flex-col gap-4 rounded-lg border border-border bg-muted/40 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Your score</p>
              <p className="text-2xl font-bold text-foreground">{score}%</p>
              <p className="mt-1 text-sm text-muted-foreground">
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
