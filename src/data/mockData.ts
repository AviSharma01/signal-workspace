import type { NewsItem, DiscussionItem } from '../shared/types'

export const mockNews: Record<string, NewsItem[]> = {
  AAPL: [
    {
      id: 'aapl-news-1',
      companyId: 'AAPL',
      headline: 'Apple Vision Pro sales exceed Q2 expectations',
      summary:
        'Analysts revised estimates upward after Apple reported stronger-than-expected demand from enterprise customers in the US and Europe.',
      source: 'Bloomberg',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 90,
    },
    {
      id: 'aapl-news-2',
      companyId: 'AAPL',
      headline: 'Apple expands AI features to older iPhone models',
      summary:
        'A software update brings on-device AI capabilities to iPhone 14 and 15 series, widening the addressable base ahead of the iPhone 17 cycle.',
      source: 'Reuters',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 5,
    },
    {
      id: 'aapl-news-3',
      companyId: 'AAPL',
      headline: 'DOJ opens new probe into App Store pricing practices',
      summary:
        "The Department of Justice is examining whether Apple's commission structure violates antitrust rules, following a similar EU investigation.",
      source: 'WSJ',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 11,
    },
  ],
  MSFT: [
    {
      id: 'msft-news-1',
      companyId: 'MSFT',
      headline: 'Microsoft Azure AI revenue grows 38% year-over-year',
      summary:
        'Cloud and AI segment continues to drive top-line growth as enterprise adoption of Copilot products accelerates across Fortune 500 customers.',
      source: 'CNBC',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 45,
    },
    {
      id: 'msft-news-2',
      companyId: 'MSFT',
      headline: 'Activision integration lifts gaming segment margins',
      summary:
        'One year post-acquisition, Activision titles have driven Game Pass subscriber growth to a record 40 million, ahead of internal targets.',
      source: 'FT',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 3,
    },
  ],
  GOOGL: [
    {
      id: 'googl-news-1',
      companyId: 'GOOGL',
      headline: 'Alphabet Search share stabilises as Gemini integration rolls out',
      summary:
        "After months of pressure from AI-native competitors, Google's search market share held steady in March, according to StatCounter data.",
      source: 'Bloomberg',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 120,
    },
    {
      id: 'googl-news-2',
      companyId: 'GOOGL',
      headline: 'Google Cloud wins multi-year contract with Deutsche Telekom',
      summary:
        "The deal, valued at approximately $1.2B, covers infrastructure migration and AI workloads, expanding Google Cloud's footprint in Europe.",
      source: 'Reuters',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 7,
    },
  ],
  AMZN: [
    {
      id: 'amzn-news-1',
      companyId: 'AMZN',
      headline: 'AWS launches new inferencing chips to compete with Nvidia',
      summary:
        "Amazon's Trainium 3 chips offer a 30% cost reduction per token for large language model inference, targeting customers looking to reduce GPU costs.",
      source: 'The Verge',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 30,
    },
    {
      id: 'amzn-news-2',
      companyId: 'AMZN',
      headline: 'Amazon Prime membership crosses 250 million globally',
      summary:
        'International expansion in Southeast Asia and Latin America pushed Prime past the milestone, with advertising revenue tied to Prime Video up 42%.',
      source: 'WSJ',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 9,
    },
  ],
  NVDA: [
    {
      id: 'nvda-news-1',
      companyId: 'NVDA',
      headline: 'Nvidia Blackwell shipments accelerate into Q2',
      summary:
        'Supply chain sources indicate Blackwell GPU allocations are tracking above initial guidance, alleviating concerns raised in the January earnings call.',
      source: 'DigiTimes',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60,
    },
    {
      id: 'nvda-news-2',
      companyId: 'NVDA',
      headline: 'China export controls weigh on Nvidia H20 demand outlook',
      summary:
        "New restrictions on H20 chip exports to China could reduce Nvidia's addressable market in the region by an estimated $4–6B annually.",
      source: 'Bloomberg',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 4,
    },
    {
      id: 'nvda-news-3',
      companyId: 'NVDA',
      headline: 'Nvidia partners with TSMC on next-gen packaging technology',
      summary:
        'The two companies are co-developing advanced chip-on-wafer-on-substrate packaging for the post-Blackwell generation, targeting 2026 production.',
      source: 'Reuters',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 8,
    },
  ],
}

export const mockDiscussion: Record<string, DiscussionItem[]> = {
  AAPL: [
    {
      id: 'aapl-disc-1',
      companyId: 'AAPL',
      title: 'Is the Vision Pro actually finding product-market fit in enterprise?',
      summary:
        'Thread debating whether the enterprise sales bump is structural demand or just early-adopter procurement cycles. Skeptics cite high per-seat cost.',
      source: 'r/investing',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 2,
    },
    {
      id: 'aapl-disc-2',
      companyId: 'AAPL',
      title: 'AAPL IV crush post-earnings — was the move priced in?',
      summary:
        'Options traders discussing implied volatility collapse after earnings beat. Consensus is the reaction was muted relative to the upside surprise.',
      source: 'r/options',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 6,
    },
  ],
  MSFT: [
    {
      id: 'msft-disc-1',
      companyId: 'MSFT',
      title: "How durable is Azure's AI growth rate as comps get harder?",
      summary:
        'Bull case: AI workloads are still in early innings. Bear case: the base effect and budget scrutiny will compress growth by H2. Mixed sentiment.',
      source: 'r/stocks',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 1,
    },
    {
      id: 'msft-disc-2',
      companyId: 'MSFT',
      title: 'Copilot adoption data — anyone seeing real enterprise pull-through?',
      summary:
        'Several enterprise IT posters report Copilot usage below expectations after the trial period. Counter-examples cited from legal and finance verticals.',
      source: 'r/investing',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 8,
    },
  ],
  GOOGL: [
    {
      id: 'googl-disc-1',
      companyId: 'GOOGL',
      title: 'Google search share stabilisation — temporary floor or trend reversal?',
      summary:
        'Community split. Some see the March data as noise. Others point to Gemini-in-search as a genuine moat improvement against Perplexity and ChatGPT.',
      source: 'r/SecurityAnalysis',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 3,
    },
    {
      id: 'googl-disc-2',
      companyId: 'GOOGL',
      title: 'GOOGL valuation: sum-of-parts still compelling at current multiples?',
      summary:
        'Model shared assigning $180 to Search/Ads, $90 to Cloud, $40 to Waymo optionality. Debate on Cloud terminal growth assumptions.',
      source: 'r/ValueInvesting',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 10,
    },
  ],
  AMZN: [
    {
      id: 'amzn-disc-1',
      companyId: 'AMZN',
      title: 'AWS Trainium vs Nvidia — does Amazon have a real alternative?',
      summary:
        'Engineers weigh in on the CUDA ecosystem moat. Most agree Trainium is cost-effective for inference-only workloads but not a full training substitute.',
      source: 'r/MachineLearning',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 2,
    },
    {
      id: 'amzn-disc-2',
      companyId: 'AMZN',
      title: 'AMZN advertising is becoming a bigger part of the story than AWS',
      summary:
        'Advertising segment grew 27% YoY. Thread explores whether ad revenue deserves a higher multiple than retail and how it rerates the stock.',
      source: 'r/investing',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 7,
    },
  ],
  NVDA: [
    {
      id: 'nvda-disc-1',
      companyId: 'NVDA',
      title: 'Blackwell supply catch-up — what does it mean for H2 ASP?',
      summary:
        'Supply normalisation historically compresses average selling prices. Bulls argue demand backlog is large enough to absorb supply without margin pressure.',
      source: 'r/stocks',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 1,
    },
    {
      id: 'nvda-disc-2',
      companyId: 'NVDA',
      title: 'China export restriction impact — $4–6B headline overstated?',
      summary:
        'Some argue Nvidia was already routing around restrictions via Singapore. Others think the H20 ban is a genuine step-change in enforcement risk.',
      source: 'r/geopolitics',
      url: '#',
      publishedAt: Date.now() - 1000 * 60 * 60 * 5,
    },
  ],
}
