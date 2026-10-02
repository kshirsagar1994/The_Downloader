import type { Metadata } from "next";
import { Header } from "../../components/Header";
import { Footer } from "../../components/Footer";
import { Scale, FileText, AlertTriangle, ShieldCheck, Globe, CheckCircle2 } from "lucide-react";

export const metadata: Metadata = {
  title: "Terms of Service & Acceptable Use — The_Downloader",
  description: "Terms of service, fair use guidelines, intellectual property responsibilities, and acceptable use policies for The_Downloader.",
};

export default function TermsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />

      <main className="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
            <Scale className="w-3.5 h-3.5" />
            Legal Agreement
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">Terms of Service & Acceptable Use</h1>
          <p className="text-sm text-muted-foreground max-w-xl mx-auto">
            Last Updated: October 2, 2026. Please read these terms carefully before using the service.
          </p>
        </div>

        <div className="space-y-6 text-sm text-muted-foreground leading-relaxed">
          {/* Section 1 */}
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              1. Description of the Service
            </h3>
            <p>
              The_Downloader provides software and technical functionality that allows users to process, retrieve, download, convert, or otherwise manage media from supported sources. The service utilizes third-party open-source components including media extraction and processing libraries. The_Downloader does not claim ownership of third-party software used by the service.
            </p>
          </div>

          {/* Section 2 */}
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              2. User Responsibility & Compliance
            </h3>
            <p>
              You are solely responsible for the content and URLs that you submit to the service and for determining whether you have the necessary rights, permissions, licenses, or other lawful authorization to access, download, copy, convert, store, or otherwise use the requested content. You must comply with all applicable local, national, and international laws and regulations.
            </p>
          </div>

          {/* Section 3 */}
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              3. Copyright and Intellectual Property
            </h3>
            <p>
              The_Downloader does not grant you ownership of any content obtained through the service. You are responsible for respecting copyright, trademark, privacy, publicity, intellectual-property, and other rights belonging to content owners and third parties. You must not use the service to infringe, misappropriate, or violate another person&apos;s intellectual-property or other legal rights.
            </p>
          </div>

          {/* Section 4 */}
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-400" />
              4. Third-Party Platforms & Terms
            </h3>
            <p>
              Content may originate from third-party websites and services. Those websites and services have their own terms of service, usage restrictions, access controls, technical restrictions, and copyright policies. Your use of The_Downloader does not override or provide permission under the terms of any third-party platform. You are responsible for complying with applicable third-party terms.
            </p>
          </div>

          {/* Section 5 */}
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              5. Prohibited Uses
            </h3>
            <ul className="list-disc list-inside space-y-1 pl-1">
              <li>Downloading or reproducing content when you do not have the necessary rights or permission.</li>
              <li>Circumventing access controls, authentication mechanisms, or security protections.</li>
              <li>Interfering with third-party systems or conducting unauthorized automated activity.</li>
              <li>Distributing infringing or unlawfully obtained content.</li>
              <li>Uploading, processing, storing, or distributing malware or malicious content.</li>
              <li>Abusing, overloading, disrupting, or attempting to compromise the service or infrastructure.</li>
            </ul>
          </div>

          {/* Section 6 & 7 */}
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground">
              6. Ephemeral Files & Service Availability
            </h3>
            <p>
              The service operates on an ephemeral storage model. All temporary files are automatically cleaned and deleted within 60 minutes after processing. The service is provided on an &quot;AS IS&quot; and &quot;AS AVAILABLE&quot; basis without guarantee of continuous or uninterrupted availability.
            </p>
          </div>

          {/* Section 8 */}
          <div className="p-6 rounded-2xl border border-border/80 bg-card/60 space-y-3">
            <h3 className="text-base font-bold text-foreground">
              7. Limitation of Liability & Contact
            </h3>
            <p>
              To the maximum extent permitted by applicable law, The_Downloader and its operators shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from the use of the service.
            </p>
            <p className="pt-2 text-xs text-muted-foreground">
              For copyright inquiries, abuse reports, or legal questions, contact the service operator through official channels.
            </p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
