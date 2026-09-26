import type { Module, User, ChecklistItem } from "./types"

export const users: User[] = [
  {
    id: "u-admin",
    name: "Jerry Okafor",
    email: "admin@firmflow.com",
    password: "admin123",
    role: "admin",
    title: "Project Manager / Architect",
    startDate: "2021-03-01",
    mentorId: null,
  },
  {
    id: "u-1",
    name: "Ava Chen",
    email: "ava@firmflow.com",
    password: "welcome",
    role: "user",
    title: "Junior Architect",
    startDate: "2026-09-14",
    mentorId: "u-mentor-1",
  },
  {
    id: "u-2",
    name: "Marcus Reed",
    email: "marcus@firmflow.com",
    password: "welcome",
    role: "user",
    title: "Architectural Designer",
    startDate: "2026-09-21",
    mentorId: "u-mentor-2",
  },
  {
    id: "u-3",
    name: "Priya Nair",
    email: "priya@firmflow.com",
    password: "welcome",
    role: "user",
    title: "BIM Specialist",
    startDate: "2026-08-04",
    mentorId: "u-mentor-1",
  },
]

export interface Mentor {
  id: string
  name: string
  title: string
  focus: string
  email: string
}

export const mentors: Mentor[] = [
  {
    id: "u-mentor-1",
    name: "Dana Whitfield",
    title: "Senior Architect",
    focus: "Design workflow, QA/QC, Revit standards",
    email: "dana@firmflow.com",
  },
  {
    id: "u-mentor-2",
    name: "Luis Moreno",
    title: "Associate Principal",
    focus: "Billing, client relations, project delivery",
    email: "luis@firmflow.com",
  },
  {
    id: "u-mentor-3",
    name: "Sokol Berisha",
    title: "Operations Lead",
    focus: "HR, payroll, office procedures",
    email: "sokol@firmflow.com",
  },
]

export const modules: Module[] = [
  {
    id: "m-day1",
    title: "Day 1 Essentials",
    category: "Getting Started",
    summary: "What you need on your very first day: access, accounts, and where to be.",
    estimatedMinutes: 15,
    day1: true,
    sections: [
      {
        id: "s1",
        heading: "Welcome to the firm",
        body: "You will receive your building badge, workstation login, and email on Day 1. Check in with the front desk and your assigned mentor before 9:00 AM.",
      },
      {
        id: "s2",
        heading: "Accounts you'll need",
        body: "Paycor (payroll), Ajera (accounting/timesheets), and your Revit/Rhino licenses. IT provisions these automatically — verify each works before end of day.",
      },
      {
        id: "s3",
        heading: "Monday morning meeting",
        body: "The whole studio meets Monday at 9:15 AM. New team members give a one-minute intro during their first Monday.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "What time is the Monday morning meeting?",
        options: ["8:00 AM", "9:15 AM", "10:30 AM", "12:00 PM"],
        correctIndex: 1,
      },
      {
        id: "q2",
        prompt: "Which system is used for timesheets and accounting?",
        options: ["Paycor", "Rhino", "Ajera", "Slack"],
        correctIndex: 2,
      },
    ],
  },
  {
    id: "m-ajera",
    title: "Ajera Accounting & Timesheets",
    category: "Finance",
    summary: "Log hours, submit timesheets, and understand project billing codes.",
    estimatedMinutes: 25,
    day1: false,
    sections: [
      {
        id: "s1",
        heading: "Logging your time",
        body: "Enter hours daily against the correct project and phase code. Timesheets are due by end of day Friday. Late entries delay client billing.",
      },
      {
        id: "s2",
        heading: "Billable vs. non-billable",
        body: "Client project work is billable. Internal training, PTO, and studio meetings use overhead codes. When unsure, ask your PM before guessing.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "When are timesheets due?",
        options: ["End of day Monday", "End of day Friday", "First of the month", "Whenever convenient"],
        correctIndex: 1,
      },
      {
        id: "q2",
        prompt: "Studio meetings should be logged as:",
        options: ["Billable client work", "An overhead code", "Not logged at all", "PTO"],
        correctIndex: 1,
      },
    ],
  },
  {
    id: "m-pto",
    title: "PTO & In/Out of Office",
    category: "HR",
    summary: "Requesting time off, marking availability, and coverage expectations.",
    estimatedMinutes: 12,
    day1: false,
    sections: [
      {
        id: "s1",
        heading: "Requesting PTO",
        body: "Submit PTO requests at least two weeks in advance through the employee portal. Your PM approves based on project deadlines.",
      },
      {
        id: "s2",
        heading: "In / out board",
        body: "Update your status on the studio in/out board when working remotely, at a site visit, or out sick so the team can reach you.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "How far in advance should PTO be requested?",
        options: ["Same day", "2 days", "At least 2 weeks", "1 month minimum"],
        correctIndex: 2,
      },
    ],
  },
  {
    id: "m-qaqc",
    title: "QA / QC Standards",
    category: "Design",
    summary: "Quality assurance and control checkpoints before drawings go out.",
    estimatedMinutes: 30,
    day1: false,
    sections: [
      {
        id: "s1",
        heading: "The review gate",
        body: "No drawing set leaves the office without a senior QA/QC review. Submit sets for review at least 48 hours before the deadline.",
      },
      {
        id: "s2",
        heading: "Keynotes & references",
        body: "Read keynotes carefully — they carry code and specification references. Cross-check every callout against the current sheet index.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "How early must a set be submitted for QA/QC?",
        options: ["2 hours", "24 hours", "At least 48 hours", "No requirement"],
        correctIndex: 2,
      },
      {
        id: "q2",
        prompt: "Keynotes primarily carry:",
        options: ["Personal notes", "Code and specification references", "Billing codes", "Meeting minutes"],
        correctIndex: 1,
      },
    ],
  },
  {
    id: "m-harassment",
    title: "Harassment Prevention",
    category: "HR",
    summary: "Required policy training on a respectful, safe workplace.",
    estimatedMinutes: 20,
    day1: false,
    sections: [
      {
        id: "s1",
        heading: "Our standard",
        body: "The firm maintains a zero-tolerance policy for harassment of any kind. Everyone is responsible for a respectful environment.",
      },
      {
        id: "s2",
        heading: "Reporting",
        body: "Concerns can be reported to any manager or directly to HR (Operations Lead). All reports are handled confidentially and without retaliation.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "Reports of harassment are handled:",
        options: ["Publicly", "Confidentially and without retaliation", "Only if witnessed", "By coworkers"],
        correctIndex: 1,
      },
    ],
  },
  {
    id: "m-billing",
    title: "Billing: Client vs. Self",
    category: "Finance",
    summary: "Distinguishing client-billable work from internal/self time.",
    estimatedMinutes: 18,
    day1: false,
    sections: [
      {
        id: "s1",
        heading: "Client billing",
        body: "Time spent producing deliverables for a client contract is billed to that project's phase codes and appears on client invoices.",
      },
      {
        id: "s2",
        heading: "Self / overhead",
        body: "Professional development, licensing study, and administrative tasks are charged to overhead, not to a client.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "Licensing study time is charged to:",
        options: ["The nearest client", "Overhead", "Whatever project is open", "It is not charged"],
        correctIndex: 1,
      },
    ],
  },
  {
    id: "m-bim",
    title: "BIM: Revit & Rhino Standards",
    category: "Design",
    summary: "Firm modeling standards, file naming, and worksharing etiquette.",
    estimatedMinutes: 35,
    day1: false,
    sections: [
      {
        id: "s1",
        heading: "File & worksharing",
        body: "Always work in your local copy and synchronize with central regularly. Never open the central model directly. Follow the firm naming convention: Project-Discipline-Sheet.",
      },
      {
        id: "s2",
        heading: "Templates & families",
        body: "Start every project from the firm Revit template. Pull families from the shared library rather than downloading from the internet.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "In Revit worksharing you should:",
        options: [
          "Open the central model directly",
          "Work locally and sync with central",
          "Email files back and forth",
          "Never sync",
        ],
        correctIndex: 1,
      },
      {
        id: "q2",
        prompt: "Where do families come from?",
        options: ["Any website", "The shared firm library", "A personal drive", "Rebuilt each time"],
        correctIndex: 1,
      },
    ],
  },
  {
    id: "m-revit-open",
    title: "Opening a Revit Model the Right Way",
    category: "Design",
    summary:
      "Hands-on: open the correct .rvt scope-of-work model as a new local file — never the central model.",
    estimatedMinutes: 15,
    day1: false,
    interactive: "revit-open",
    sections: [
      {
        id: "s1",
        heading: "Why this matters",
        body: "The central model is the single source of truth for the whole team. Opening it directly and editing it risks corrupting everyone's work. You always create your own local copy to work in and sync your changes back to central.",
      },
      {
        id: "s2",
        heading: "Find the scope-of-work model",
        body: "A project folder often holds several .rvt files. The central model is named with _CENTRAL. Your task model — the scope of work — is renamed for your discipline or package (for example _SOW-Interiors). Open that one, not the central.",
      },
      {
        id: "s3",
        heading: "Always Create New Local",
        body: "In the Open dialog, tick 'Create New Local' before clicking Open. Revit copies the central model to your machine so you work locally and synchronize safely — this is the step people most often forget.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "Which file should you open to start working?",
        options: [
          "The _CENTRAL model",
          "The scope-of-work model (e.g. _SOW-Interiors)",
          "Any .rvt in the folder",
          "A _backup file",
        ],
        correctIndex: 1,
      },
      {
        id: "q2",
        prompt: "Before clicking Open, you must enable:",
        options: ["Audit", "Detach from Central", "Create New Local", "Nothing"],
        correctIndex: 2,
      },
      {
        id: "q3",
        prompt: "Why never open the central model directly?",
        options: [
          "It is slower to load",
          "You risk corrupting the team's shared source of truth",
          "It is read-only anyway",
          "It has no families loaded",
        ],
        correctIndex: 1,
      },
    ],
  },
  {
    id: "m-office",
    title: "Opening & Closing the Office",
    category: "Operations",
    summary: "Procedures for the first and last person in the studio each day.",
    estimatedMinutes: 10,
    day1: false,
    sections: [
      {
        id: "s1",
        heading: "Opening",
        body: "Disarm the alarm with your code, unlock the front entrance, turn on studio lighting and the plotter, and start the coffee.",
      },
      {
        id: "s2",
        heading: "Closing",
        body: "Ensure all workstations are logged off, the plotter is idle, lights are off, doors are locked, and the alarm is armed before leaving.",
      },
    ],
    quiz: [
      {
        id: "q1",
        prompt: "Before leaving as the last person, you must:",
        options: ["Leave lights on for security", "Arm the alarm and lock up", "Leave the plotter running", "Nothing specific"],
        correctIndex: 1,
      },
    ],
  },
]

export const defaultChecklist: ChecklistItem[] = [
  { id: "c1", label: "Pick up building badge from front desk", done: false },
  { id: "c2", label: "Verify Paycor, Ajera, and Revit/Rhino logins", done: false },
  { id: "c3", label: "Complete i9 / W4 in Paycor", done: false },
  { id: "c4", label: "Meet your assigned mentor", done: false },
  { id: "c5", label: "Attend your first Monday morning meeting", done: false },
  { id: "c6", label: "Finish all Day 1 Essentials", done: false },
]
