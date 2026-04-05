import { useEffect, useRef, useState } from "react";

const integrations = [
  { name: "Zoom" },
  { name: "Google Meet" },
  { name: "Slack" },
  { name: "GitHub" },
  { name: "Google Calendar" },
  { name: "Web Search" },
];

const Integrations = () => {
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
          }
        });
      },
      { threshold: 0.2 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="py-24 bg-background overflow-hidden">
      <div className="container mx-auto px-6">
        <div className={`text-center mb-16 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-4 font-display">
            Works with your favorite tools
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Nemo seamlessly integrates with the platforms you already use every day.
          </p>
        </div>

        <div className={`relative transition-all duration-700 delay-300 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
          <div className="flex overflow-hidden">
            <div className="flex animate-marquee whitespace-nowrap">
              {[...integrations, ...integrations].map((integration, index) => (
                <div
                  key={index}
                  className="mx-8 flex items-center justify-center"
                >
                  <span className="text-2xl font-semibold text-muted-foreground/60 hover:text-muted-foreground transition-colors duration-300">
                    {integration.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Integrations;
