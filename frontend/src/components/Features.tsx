import { Bot, Search, Calendar, Github, TrendingUp, MessageSquare } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const features = [
  {
    icon: Bot,
    title: "Real-Time AI Assistant",
    description: "Nemo joins your meetings and responds to questions instantly using live transcriptions and powerful LLM technology.",
  },
  {
    icon: Search,
    title: "Web-Powered Intelligence",
    description: "Access up-to-date information during meetings with integrated web search capabilities.",
  },
  {
    icon: Github,
    title: "GitHub Integration",
    description: "Automatically update issues, track tasks, and manage repositories directly from your meetings.",
  },
  {
    icon: Calendar,
    title: "Calendar Sync",
    description: "Seamlessly manage Google Calendar events and schedule follow-ups without leaving your call.",
  },
  {
    icon: TrendingUp,
    title: "Smart Analysis",
    description: "Ask Nemo to analyze data and provide insights: 'List the five biggest issues in my latest repository.'",
  },
  {
    icon: MessageSquare,
    title: "Context-Aware",
    description: "Nemo understands meeting topics and goals, ensuring your team stays focused and on track.",
  },
];

const Features = () => {
  const [visibleCards, setVisibleCards] = useState<number[]>([]);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            features.forEach((_, index) => {
              setTimeout(() => {
                setVisibleCards((prev) => [...prev, index]);
              }, index * 100);
            });
          }
        });
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="py-24 bg-gradient-to-b from-background to-secondary/30">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-4">
            Everything you need in a meeting assistant
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Nemo combines cutting-edge AI with practical integrations to transform how your team collaborates.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className={`bg-card rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border border-border hover:border-primary/50 ${
                  visibleCards.includes(index) ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
                }`}
                style={{
                  transition: 'opacity 0.6s ease-out, transform 0.6s ease-out',
                }}
              >
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center mb-6 shadow-md">
                  <Icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-semibold text-card-foreground mb-3">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;
