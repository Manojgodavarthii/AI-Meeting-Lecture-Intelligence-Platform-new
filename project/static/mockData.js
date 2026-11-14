// Mock Data for EchoAction AI Platform
window.MeetingActionPlatform = window.MeetingActionPlatform || {};

window.MeetingActionPlatform.mockMeetings = [
  {
    id: "meet-1",
    title: "Backend API & Caching Sync",
    category: "Sprint Planning",
    date: "June 8, 2026",
    duration: "12m 45s",
    attendees: ["Sarah (Lead Backend)", "Alex (DevOps)", "Marcus (Frontend)"],
    audioUrl: "#",
    summary: {
      overview: "The team synced on addressing database query bottlenecks by implementing Redis caching for the user feed endpoints. Alex will set up the Redis cluster on staging, Marcus will update the frontend API client for cache headers, and Sarah will document the changes in Confluence. Load tests will be conducted to verify performance improvements.",
      keyPoints: [
        "User feed database queries are currently timing out under heavy loads, causing high latency.",
        "Redis will be introduced on the staging environment first to validate the caching strategy.",
        "Frontend needs to be updated to support Cache-Control headers (ETag, Last-Modified) for efficient validation.",
        "Sarah will provide documentation for the header definitions to assist the frontend implementation.",
        "k6 load testing will be used to benchmark performance improvements under simulated load."
      ],
      sentiment: "Productive & Collaborative (Positive)",
      meetingScore: 92
    },
    actionItems: [
      {
        id: "task-1",
        title: "Spin up Redis cluster on staging environment",
        assignee: "Alex (DevOps)",
        avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "High",
        deadline: "2026-06-10",
        status: "Pending",
        category: "Infrastructure",
        matchKeywords: ["redis", "cluster", "staging", "spin up"]
      },
      {
        id: "task-2",
        title: "Update frontend API client with Cache-Control headers",
        assignee: "Marcus (Frontend)",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "Medium",
        deadline: "2026-06-12",
        status: "Pending",
        category: "Frontend",
        matchKeywords: ["caching", "cache-control", "axios", "wrapper", "header", "api client"]
      },
      {
        id: "task-3",
        title: "Document header changes in Confluence wiki",
        assignee: "Sarah (Lead Backend)",
        avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "Low",
        deadline: "2026-06-09",
        status: "Pending",
        category: "Documentation",
        matchKeywords: ["confluence", "document", "header", "wiki", "changes"]
      },
      {
        id: "task-4",
        title: "Run k6 load tests on cached vs uncached routes",
        assignee: "Alex (DevOps)",
        avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "Medium",
        deadline: "2026-06-15",
        status: "Pending",
        category: "QA/Testing",
        matchKeywords: ["load tests", "k6", "concurrency", "test"]
      }
    ],
    jiraTickets: [
      {
        id: "JIRA-101",
        title: "Spin up Redis cluster on staging environment",
        type: "Story",
        priority: "High",
        assignee: "Alex (DevOps)",
        description: "Deploy a Redis cluster on the Kubernetes staging environment. Set appropriate memory limits and ensure connection pooling is configured. Integrate connection strings into the API secret configuration."
      },
      {
        id: "JIRA-102",
        title: "Update frontend API client with Cache-Control headers",
        type: "Story",
        priority: "Medium",
        assignee: "Marcus (Frontend)",
        description: "Configure axios client wrapper to respect Cache-Control response headers (ETag, Last-Modified) and store local cached state. Implement revalidation checks (If-None-Match)."
      },
      {
        id: "JIRA-103",
        title: "Document header changes in Confluence",
        type: "Task",
        priority: "Low",
        assignee: "Sarah (Lead Backend)",
        description: "Draft a Confluence wiki page documenting the updated REST API headers, status codes, and cache validation requirements for client integration."
      }
    ],
    emailDraft: {
      subject: "Meeting Summary & Actions: Backend API & Caching Sync",
      body: `Hi Team,

Here is a summary of the action items and key decisions from today's sync regarding the API bottlenecks:

Key Decisions:
- We are moving forward with Redis caching on the feed endpoints starting on staging.
- Client validation headers (ETag/Last-Modified) will be introduced for smarter caching.

Action Items:
1. Alex: Spin up the Redis cluster on staging by June 10.
2. Marcus: Update frontend API client for cache headers by June 12.
3. Sarah: Document the new headers on Confluence by June 9.
4. Alex: Run k6 load tests on cached/uncached routes by June 15.

We'll follow up on Slack as these progress.

Best,
Sarah`
    },
    transcript: [
      { speaker: "Sarah (Lead Backend)", time: "0:05", text: "Alright, let's sync on the API bottlenecks. The database queries for fetching user feeds are timing out under heavy loads." },
      { speaker: "Alex (DevOps)", time: "0:28", text: "Yeah, we need to implement Redis caching on the feed endpoints. I can spin up the Redis cluster on staging by Wednesday." },
      { speaker: "Sarah (Lead Backend)", time: "0:52", text: "Perfect. Marcus, we'll need you to update the frontend API client to support cache validation headers, like ETag or Last-Modified." },
      { speaker: "Marcus (Frontend)", time: "1:15", text: "Sure. I can add cache-control support to our axios wrapper. I'll need some documentation on the new headers though." },
      { speaker: "Sarah (Lead Backend)", time: "1:40", text: "I'll document the endpoint header changes in Confluence by tomorrow afternoon. Let's make sure we test it with high concurrency." },
      { speaker: "Alex (DevOps)", time: "2:05", text: "I'll also run some load tests using k6 to compare cached vs uncached routes once caching is live." },
      { speaker: "Sarah (Lead Backend)", time: "2:25", text: "Great plan. Let's touch base on Thursday to review progress." }
    ]
  },
  {
    id: "meet-2",
    title: "UX Design & Landing Page Sync",
    category: "Design Sync",
    date: "June 7, 2026",
    duration: "18m 20s",
    attendees: ["Elena (Lead Designer)", "Marcus (Frontend)", "Chloe (Product Manager)"],
    audioUrl: "#",
    summary: {
      overview: "The team reviewed the landing page redesign mockup in Figma. Elena shared the dark mode design. Marcus will integrate the CSS color variables and implement the header survey link. Elena will complete the mobile layouts and collapsible menu transitions.",
      keyPoints: [
        "The dark mode design system was approved, focusing on glassmorphism and subtle glowing borders.",
        "Elena will export design tokens as CSS variables for clean developer handoff.",
        "Marcus will link the website header feedback button to HubSpot survey form.",
        "Elena will finish the mobile layouts and transition specs to ensure a high-quality responsive build."
      ],
      sentiment: "Creative & Design-Focused (Very Positive)",
      meetingScore: 95
    },
    actionItems: [
      {
        id: "task-5",
        title: "Export Figma design tokens to CSS variables",
        assignee: "Elena (Lead Designer)",
        avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "Medium",
        deadline: "2026-06-08",
        status: "Pending",
        category: "Design",
        matchKeywords: ["figma", "tokens", "variables", "export"]
      },
      {
        id: "task-6",
        title: "Integrate CSS design tokens into main stylesheet",
        assignee: "Marcus (Frontend)",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "High",
        deadline: "2026-06-09",
        status: "Pending",
        category: "Frontend",
        matchKeywords: ["stylesheet", "integrate", "variables", "css", "tokens"]
      },
      {
        id: "task-7",
        title: "Implement header survey feedback link",
        assignee: "Marcus (Frontend)",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "Low",
        deadline: "2026-06-11",
        status: "Pending",
        category: "Frontend",
        matchKeywords: ["survey", "feedback link", "hubspot", "navbar", "header link"]
      },
      {
        id: "task-8",
        title: "Complete mobile design frames and menu transitions",
        assignee: "Elena (Lead Designer)",
        avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "Medium",
        deadline: "2026-06-09",
        status: "Pending",
        category: "Design",
        matchKeywords: ["mobile", "frames", "collapsible", "menu", "transitions"]
      }
    ],
    jiraTickets: [
      {
        id: "JIRA-201",
        title: "Integrate CSS design tokens into main stylesheet",
        type: "Story",
        priority: "High",
        assignee: "Marcus (Frontend)",
        description: "Apply design tokens (colors, font-sizes, shadows, borders) exported from Figma variables into the global CSS style variables file."
      },
      {
        id: "JIRA-202",
        title: "Implement header survey feedback link",
        type: "Task",
        priority: "Low",
        assignee: "Marcus (Frontend)",
        description: "Add a 'Give Feedback' button in the landing page header pointing to the HubSpot survey form. Ensure custom click tracking is active."
      }
    ],
    emailDraft: {
      subject: "Design Alignment & Next Steps: Landing Page UX",
      body: `Hi Team,

Here's the plan following today's review of the landing page mockups:

Key Updates:
- The new dark theme and glassmorphism styling look awesome and are approved.
- Elena is finalizing mobile transitions to maintain consistent branding.

Tasks Assigned:
1. Elena: Export CSS variables from Figma (due Jun 8).
2. Marcus: Integrate variables into project stylesheet (due Jun 9).
3. Marcus: Add survey feedback link to website header (due Jun 11).
4. Elena: Finish mobile layout specification frames (due Jun 9).

Let's make sure code matches mockup design elements exactly.

Thanks,
Chloe`
    },
    transcript: [
      { speaker: "Chloe (Product Manager)", time: "0:05", text: "Thanks for jumping on the call. We need to finalize the mockups for the landing page before the developer handoff." },
      { speaker: "Elena (Lead Designer)", time: "0:35", text: "I've updated the Figma prototype with the new dark mode design system. I added glassmorphism cards and smooth hover effects." },
      { speaker: "Marcus (Frontend)", time: "1:08", text: "This looks stunning, Elena! The gradients are really smooth. Are the color tokens updated in Figma?" },
      { speaker: "Elena (Lead Designer)", time: "1:35", text: "Yes, I structured them into variables. I'll export the CSS variables list so you can drop them right into your stylesheet." },
      { speaker: "Chloe (Product Manager)", time: "2:02", text: "We need the feedback link added to the header. Let's make sure it opens the HubSpot survey form." },
      { speaker: "Marcus (Frontend)", time: "2:30", text: "No problem, I can implement the navbar link and link it to our HubSpot form." },
      { speaker: "Elena (Lead Designer)", time: "2:55", text: "I'll also double check the mobile responsiveness. I need to design the collapsible menu transitions. I'll upload those mobile frames by tonight." }
    ]
  },
  {
    id: "meet-3",
    title: "Marketing Campaign Kickoff",
    category: "Strategy",
    date: "June 5, 2026",
    duration: "15m 10s",
    attendees: ["Chloe (Product Manager)", "Dan (Marketing Lead)", "Sophia (Content Writer)"],
    audioUrl: "#",
    summary: {
      overview: "The marketing team aligned on the Q3 launch schedule. Dan will draft ad copy for google and meta networks. Sophia will prepare a blog post illustrating our auto-completion feature. Dan will draft the Mixpanel event tracking specification doc.",
      keyPoints: [
        "Product launch is targeted for mid-July.",
        "Advertising campaign will focus on the unique auto-task-completion tracker capability.",
        "Sophia will write a comprehensive article detailing how Whisper transcripts parse updates.",
        "Analytics schema must track conversions across sign-up steps using Mixpanel."
      ],
      sentiment: "Energetic & Forward-Looking (Positive)",
      meetingScore: 88
    },
    actionItems: [
      {
        id: "task-9",
        title: "Draft Q3 ad copies for Google and Meta Ads",
        assignee: "Dan (Marketing Lead)",
        avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "Medium",
        deadline: "2026-06-12",
        status: "Pending",
        category: "Marketing",
        matchKeywords: ["ad copy", "ads", "google", "meta"]
      },
      {
        id: "task-10",
        title: "Write launch blog post highlighting task tracking",
        assignee: "Sophia (Content Writer)",
        avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "High",
        deadline: "2026-06-11",
        status: "Pending",
        category: "Content",
        matchKeywords: ["blog post", "article", "newsletter", "blog"]
      },
      {
        id: "task-11",
        title: "Write Mixpanel event tracking specification doc",
        assignee: "Dan (Marketing Lead)",
        avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80",
        priority: "Medium",
        deadline: "2026-06-10",
        status: "Pending",
        category: "Analytics",
        matchKeywords: ["mixpanel", "tracking", "spec", "events"]
      }
    ],
    jiraTickets: [
      {
        id: "JIRA-301",
        title: "Write launch blog post highlighting task tracking",
        type: "Story",
        priority: "High",
        assignee: "Sophia (Content Writer)",
        description: "Draft a 1200-word product launch article explaining user workflow improvements and automatic task completion checks."
      },
      {
        id: "JIRA-302",
        title: "Write Mixpanel event tracking specification doc",
        type: "Task",
        priority: "Medium",
        assignee: "Dan (Marketing Lead)",
        description: "Outline data requirements for funnel tracking, including button-clicks, sign-up events, and vector search query latency."
      }
    ],
    emailDraft: {
      subject: "Q3 Campaign Plan & Deliverables: Kickoff",
      body: `Hi Marketing Team,

Excited to kick off our launch planning for the EchoAction platform. Here are the immediate tasks:

- Dan: Draft advertising headlines and descriptions for search/social (Jun 12).
- Sophia: Write a technical marketing blog post highlighting our auto-task completion (Jun 11).
- Dan: Create the tracking spec sheet for analytics implementation (Jun 10).

We will meet next week to review drafts and media copy.

Best,
Chloe`
    },
    transcript: [
      { speaker: "Chloe (Product Manager)", time: "0:05", text: "Let's outline our Q3 marketing launch plan. We have the product release scheduled for mid-July." },
      { speaker: "Dan (Marketing Lead)", time: "0:42", text: "I've started drafting the ad copy for Google Ads and Meta. We want to highlight the automatic task completion tracking as our hook." },
      { speaker: "Sophia (Content Writer)", time: "1:10", text: "Excellent, that feature is a huge differentiator. I can write a detailed blog post detailing how it works under the hood." },
      { speaker: "Dan (Marketing Lead)", time: "1:38", text: "Awesome. I'll need you to draft the blog post by Thursday, Sophia. Then I'll schedule the email newsletter announcement." },
      { speaker: "Sophia (Content Writer)", time: "2:05", text: "Sounds good. I'll focus on the AI integration aspects, especially the Llama and Whisper parts." },
      { speaker: "Chloe (Product Manager)", time: "2:30", text: "We also need to define our analytics goals. We should set up Mixpanel event tracking for the signup funnel." },
      { speaker: "Dan (Marketing Lead)", time: "3:02", text: "I can write the analytics spec doc specifying what custom events we need to track." }
    ]
  }
];

window.MeetingActionPlatform.mockVideoMeetings = [
  {
    id: "vid-1",
    title: "Q3 Product Roadmap Presentation",
    category: "Presentation",
    date: "June 14, 2026",
    metadata: {
      duration: "18m 42s",
      duration_seconds: 1122,
      resolution: "1920x1080",
      fps: 30,
      video_codec: "H264",
      audio_codec: "AAC",
      size_mb: 284.5
    },
    chapters: [
      { index: 1, title: "Introduction & Overview", timestamp_start: "0:00", timestamp_end: "3:44", color: "#6366f1", summary: "Sarah opens the Q3 product roadmap presentation, setting context for the team's goals and current sprint velocity." },
      { index: 2, title: "Feature Prioritization", timestamp_start: "3:44", timestamp_end: "7:29", color: "#06b6d4", summary: "The team discusses priority ranking for the new video analysis module and semantic search improvements." },
      { index: 3, title: "Timeline & Milestones", timestamp_start: "7:29", timestamp_end: "11:14", color: "#10b981", summary: "Alex walks through the delivery milestones and infrastructure requirements for the Q3 launch window." },
      { index: 4, title: "Stakeholder Alignment", timestamp_start: "11:14", timestamp_end: "14:58", color: "#f59e0b", summary: "Marketing and design alignment is confirmed. Elena presents updated brand guidelines for the release." },
      { index: 5, title: "Next Steps & Wrap-Up", timestamp_start: "14:58", timestamp_end: "18:42", color: "#f43f5e", summary: "Action items are assigned and the team aligns on the weekly check-in schedule for the remainder of Q3." }
    ],
    summary: {
      overview: "Sarah led the Q3 product roadmap presentation. The team aligned on priority features including video analysis, semantic search upgrades, and the mobile app beta. Alex outlined infrastructure scaling plans and Elena confirmed design system readiness for the launch.",
      keyPoints: [
        "Video analysis module is the top priority feature for Q3, targeting the mid-July release.",
        "Semantic search improvements include vector indexing for transcript data.",
        "Alex will provision additional GPU capacity on staging for Whisper workloads.",
        "Elena confirmed the updated brand design system is ready for developer handoff.",
        "Weekly check-ins confirmed every Thursday at 3 PM EST."
      ],
      sentiment: "Strategic & Aligned (Very Positive)",
      meetingScore: 94
    },
    actionItems: [
      { id: "vtask-1", title: "Provision GPU staging environment for Whisper video processing", assignee: "Alex (DevOps)", avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "High", deadline: "2026-06-18", status: "Pending", category: "Infrastructure", matchKeywords: ["gpu", "staging", "whisper"] },
      { id: "vtask-2", title: "Complete video analysis frontend UI components", assignee: "Marcus (Frontend)", avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "High", deadline: "2026-06-20", status: "Pending", category: "Frontend", matchKeywords: ["video", "ui", "components"] },
      { id: "vtask-3", title: "Export updated brand design tokens to CSS variables", assignee: "Elena (Lead Designer)", avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "Medium", deadline: "2026-06-16", status: "Pending", category: "Design", matchKeywords: ["design", "tokens", "brand"] }
    ],
    transcript: "Good morning everyone, Sarah here. Today we are covering the Q3 product roadmap. Our main focus is video analysis, which the team has been requesting for months. Moving on to feature prioritization, we have ranked video analysis as our top priority for this quarter. Additionally, we are upgrading our semantic search capabilities with vector indexing. Next, let me hand it over to Alex for the infrastructure timeline. Alex will provision additional GPU capacity on the staging server specifically for the Whisper video transcription workload. Finally, Elena confirmed the design system is ready and the brand guidelines have been updated. Our next steps are clear: video analysis UI by June 20, infrastructure by June 18, and brand tokens exported by June 16. Let us touch base every Thursday."
  },
  {
    id: "vid-2",
    title: "AI Architecture Deep Dive",
    category: "Technical Review",
    date: "June 10, 2026",
    metadata: {
      duration: "24m 15s",
      duration_seconds: 1455,
      resolution: "2560x1440",
      fps: 60,
      video_codec: "H265",
      audio_codec: "OPUS",
      size_mb: 512.8
    },
    chapters: [
      { index: 1, title: "Architecture Goals", timestamp_start: "0:00", timestamp_end: "4:51", color: "#6366f1", summary: "The team reviews the current AI pipeline architecture and identifies bottlenecks in the transcription pipeline." },
      { index: 2, title: "Whisper Model Comparison", timestamp_start: "4:51", timestamp_end: "9:42", color: "#06b6d4", summary: "Benchmarking results for Whisper base, small, and medium models are reviewed across different content types." },
      { index: 3, title: "Vector Search Design", timestamp_start: "9:42", timestamp_end: "14:33", color: "#10b981", summary: "The semantic search layer design is presented including chunking strategy and embedding model selection." },
      { index: 4, title: "Scaling & Performance", timestamp_start: "14:33", timestamp_end: "19:24", color: "#f59e0b", summary: "Discussion of horizontal scaling options and GPU memory optimization for concurrent video processing." },
      { index: 5, title: "Implementation Roadmap", timestamp_start: "19:24", timestamp_end: "24:15", color: "#f43f5e", summary: "The team agrees on a phased rollout plan starting with single-video processing before parallel queue support." }
    ],
    summary: {
      overview: "Deep technical review of the AI transcription and semantic search architecture. The team benchmarked Whisper model variants, finalized the vector embedding strategy using FAISS for local search, and agreed on a phased GPU scaling plan to support concurrent video analysis workloads.",
      keyPoints: [
        "Whisper 'small' model provides the best accuracy-to-speed tradeoff for meeting recordings.",
        "FAISS will be used for local vector indexing with optional Pinecone migration path.",
        "Chunking strategy: 512-token windows with 64-token overlap for semantic search.",
        "GPU horizontal scaling will use Kubernetes job queues with Redis task routing.",
        "Phase 1 targets single-video sequential processing; Phase 2 adds parallel queues."
      ],
      sentiment: "Technical & Problem-Solving (Positive)",
      meetingScore: 89
    },
    actionItems: [
      { id: "vtask-4", title: "Implement FAISS vector index for transcript semantic search", assignee: "Sarah (Lead Backend)", avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "High", deadline: "2026-06-22", status: "Pending", category: "Backend", matchKeywords: ["faiss", "vector", "search"] },
      { id: "vtask-5", title: "Upgrade Whisper model from base to small on production", assignee: "Alex (DevOps)", avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "High", deadline: "2026-06-19", status: "Pending", category: "Infrastructure", matchKeywords: ["whisper", "model", "upgrade"] },
      { id: "vtask-6", title: "Design Redis task queue schema for video processing jobs", assignee: "Sarah (Lead Backend)", avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "Medium", deadline: "2026-06-24", status: "Pending", category: "Backend", matchKeywords: ["redis", "queue", "jobs"] }
    ],
    transcript: "Let us start with our architecture goals for the AI pipeline. The first challenge is latency in the transcription step. Second, we need to address memory consumption during concurrent video jobs. Now, moving on to the Whisper model comparison. The benchmarks clearly show the small model is the best tradeoff for our meeting content. Third item on the agenda is the vector search design. We have decided on FAISS with 512-token chunking and 64-token overlap. Additionally, the scaling approach will use Kubernetes job queues routed through Redis. Finally, the implementation roadmap is phased. Starting with single-video sequential processing, then adding parallel queue support in Phase 2. The next steps include implementing FAISS by June 22, upgrading Whisper to small by June 19, and designing the Redis schema by June 24."
  },
  {
    id: "vid-3",
    title: "Team Retrospective & Sprint Review",
    category: "Retrospective",
    date: "June 6, 2026",
    metadata: {
      duration: "12m 08s",
      duration_seconds: 728,
      resolution: "1280x720",
      fps: 30,
      video_codec: "VP9",
      audio_codec: "OPUS",
      size_mb: 98.2
    },
    chapters: [
      { index: 1, title: "Sprint Outcomes Review", timestamp_start: "0:00", timestamp_end: "3:02", color: "#6366f1", summary: "The team reviews completed sprint stories and velocity metrics from the last two-week cycle." },
      { index: 2, title: "What Went Well", timestamp_start: "3:02", timestamp_end: "6:04", color: "#06b6d4", summary: "Team highlights successful collaboration, fast PR reviews, and the on-time design system delivery." },
      { index: 3, title: "Improvement Areas", timestamp_start: "6:04", timestamp_end: "9:06", color: "#10b981", summary: "Discussion of communication gaps and test coverage issues identified during the sprint." },
      { index: 4, title: "Action Items & Commitments", timestamp_start: "9:06", timestamp_end: "12:08", color: "#f59e0b", summary: "The team commits to improvement actions including daily async standups and code review checklists." }
    ],
    summary: {
      overview: "The sprint retrospective covered completed stories, velocity trends, and team morale. The sprint delivered 34 of 38 story points. Key highlights include fast PR turnaround and on-time design delivery. Improvement areas focus on async communication and test coverage gaps.",
      keyPoints: [
        "Sprint velocity: 34/38 story points completed — 89% completion rate.",
        "PR review turnaround improved from 48h to under 24h this sprint.",
        "Design system was delivered two days ahead of schedule.",
        "Test coverage dropped to 71% — team commits to targeting 80% minimum.",
        "Async standup bot will be implemented in Slack to reduce meeting overhead."
      ],
      sentiment: "Reflective & Constructive (Positive)",
      meetingScore: 85
    },
    actionItems: [
      { id: "vtask-7", title: "Set up async standup Slack bot for daily updates", assignee: "Alex (DevOps)", avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "Medium", deadline: "2026-06-09", status: "Pending", category: "Process", matchKeywords: ["slack", "standup", "bot"] },
      { id: "vtask-8", title: "Increase test coverage from 71% to 80% minimum", assignee: "Marcus (Frontend)", avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "High", deadline: "2026-06-13", status: "Pending", category: "QA/Testing", matchKeywords: ["test", "coverage", "qa"] },
      { id: "vtask-9", title: "Create PR review checklist template in GitHub", assignee: "Sarah (Lead Backend)", avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80", priority: "Low", deadline: "2026-06-11", status: "Pending", category: "Process", matchKeywords: ["pr", "review", "checklist"] }
    ],
    transcript: "Starting our retrospective with the sprint outcomes. We completed 34 of 38 story points this cycle. The first highlight is our PR turnaround, which improved significantly to under 24 hours. Second, Elena delivered the design system two days ahead of schedule, which was great. Now moving on to improvement areas. The key point is that our test coverage dropped to 71 percent. We need to address this urgently. Additionally, async communication had some gaps this sprint. Finally, our action items: Alex will set up the async standup Slack bot, Marcus commits to raising test coverage to 80 percent minimum, and Sarah will create a standardized PR review checklist template in GitHub. Thank you all for a productive retrospective."
  }
];

window.MeetingActionPlatform.devActivities = [
  {
    id: "act-1",
    type: "git",
    author: "Alex (DevOps)",
    source: "Git Commit",
    text: "feat(infra): spin up Redis cluster on staging environment",
    timestamp: "Just now",
    taskId: "task-1"
  },
  {
    id: "act-2",
    type: "git",
    author: "Marcus (Frontend)",
    source: "Git Commit",
    text: "refactor(style): integrate CSS design tokens into main stylesheet",
    timestamp: "10 mins ago",
    taskId: "task-6"
  },
  {
    id: "act-3",
    type: "slack",
    author: "Marcus (Frontend)",
    source: "Slack Sync",
    text: "Hey Chloe, I just finished implementing the header survey feedback link pointing to HubSpot!",
    timestamp: "25 mins ago",
    taskId: "task-7"
  },
  {
    id: "act-4",
    type: "slack",
    author: "Elena (Lead Designer)",
    source: "Slack Sync",
    text: "Just uploaded the mobile design frames and collapsible menu spec files to Figma.",
    timestamp: "1 hour ago",
    taskId: "task-8"
  },
  {
    id: "act-5",
    type: "git",
    author: "Sophia (Content Writer)",
    source: "Git Commit",
    text: "docs: write launch blog post highlighting task tracking capabilities",
    timestamp: "2 hours ago",
    taskId: "task-10"
  },
  {
    id: "act-6",
    type: "slack",
    author: "Dan (Marketing Lead)",
    source: "Slack Sync",
    text: "Completed writing the Mixpanel event tracking specification doc and shared on Google Drive.",
    timestamp: "4 hours ago",
    taskId: "task-11"
  }
];
