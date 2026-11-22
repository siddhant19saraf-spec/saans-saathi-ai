import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const faqs = [
  {
    value: "live",
    question: "Is this showing live air quality?",
    answer:
      "It depends on the provider shown. Open-Meteo returns model-based forecast data, which every surface labels as model output rather than a measurement. Ground-station observations come from OpenAQ when an API key is configured; coverage is incomplete, so no nearby station is guaranteed. The CPCB adapter reports an unavailable status because its official data-access endpoint could not be verified.",
  },
  {
    value: "standard",
    question: "Which AQI standard is used?",
    answer:
      "The primary index is the CPCB 2014 National AQI used in India. It is computed only when the required averaging windows and pollutant count are satisfied; otherwise the API returns the reason an overall AQI is unavailable. When a provider also returns a US or European AQI, those numbers appear separately and are labelled with their own scale. They are never mixed or re-mapped.",
  },
  {
    value: "source",
    question: "Where does the data come from?",
    answer:
      "From air-quality providers called through the backend, with provider name, source type, observation time, fetch time, age and attribution shown next to the reading. Model values and ground-station observations are kept separate. Monitoring stations are never invented.",
  },
  {
    value: "privacy",
    question: "Where is my household information stored?",
    answer:
      "The household profile, activity preferences and recommendation history are stored in the SAANS SAATHI database under an anonymous session token kept in this browser. Routines, impact logs, checklist progress and notification preferences stay in localStorage. There is no account, name, email or phone number, and the family page can delete the profile or the whole session.",
  },
  {
    value: "key",
    question: "Is the Gemini API key exposed to the browser?",
    answer:
      "No. The key is read only by the backend configuration and is never placed in a NEXT_PUBLIC_ variable. The copilot page does not contain any key or call Gemini directly.",
  },
  {
    value: "mobile",
    question: "Does it work on a phone?",
    answer:
      "Yes. The workspace uses a slide-over navigation drawer on small screens, responsive grids, and touch-friendly controls. Tables and charts provide text alternatives for assistive technology.",
  },
];

export function FaqSection() {
  return (
    <section id="faq" aria-labelledby="faq-heading" className="border-b border-line">
      <div className="mx-auto grid w-full max-w-6xl gap-10 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[0.8fr_1.2fr] lg:px-8">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-brand-700 uppercase">FAQ</p>
          <h2
            id="faq-heading"
            className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl"
          >
            Straight answers
          </h2>
          <p className="mt-3 text-base leading-relaxed text-ink-muted">
            What this build does, what it does not do, and how it will handle data once services are
            connected.
          </p>
        </div>

        <Accordion
          type="single"
          collapsible
          className="rounded-2xl border border-line bg-white px-5"
        >
          {faqs.map((faq) => (
            <AccordionItem key={faq.value} value={faq.value}>
              <AccordionTrigger>{faq.question}</AccordionTrigger>
              <AccordionContent>{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
