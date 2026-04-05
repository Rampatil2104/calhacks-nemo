import { Monitor, Puzzle, Zap } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const roadmapItems = [
  {
    icon: Monitor,
    title: "Screen Sharing",
    description: "Nemo will be able to share its screen to present information and visualizations directly in meetings.",
  },
  {
    icon: Puzzle,
    title: "Expanded MCP Integrations",
    description: "Connect with even more tools and services to automate your entire workflow.",
  },
  {
    icon: Zap,
    title: "Zero-Shot Classification",
    description: "Advanced models to reduce latency by intelligently routing queries to the right handlers.",
  },
];

const Roadmap = () => {
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
    <section ref={sectionRef} className="py-24 bg-gradient-to-b from-secondary/30 to-background">
      <div className="container mx-auto px-6">
        <div className={`text-center mb-16 transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <div className="inline-block mb-4 px-4 py-2 bg-primary/10 rounded-full border border-primary/20">
            <span className="text-primary text-sm font-medium">Coming Soon</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-4">
            What's on the horizon
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            We're constantly evolving to make Nemo even more powerful and versatile.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {roadmapItems.map((item, index) => {
            const Icon = item.icon;
            return (
              <div
                key={index}
                className={`bg-card rounded-2xl p-8 shadow-md border border-border hover:border-primary/50 transition-all duration-500 ${
                  isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
                }`}
                style={{
                  transitionDelay: `${index * 150}ms`,
                }}
              >
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center mb-6">
                  <Icon className="w-8 h-8 text-primary" />
                </div>
                <h3 className="text-2xl font-semibold text-card-foreground mb-3">
                  {item.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {item.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Roadmap;
