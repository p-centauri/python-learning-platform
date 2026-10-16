import { Shell } from "@/components/shell";
export default function AcademyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Shell>{children}</Shell>;
}
