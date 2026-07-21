const guideSections = [
  {
    title: '1. Workbook Intake',
    body: 'Upload an RVTools workbook or start with samples/rvtools-small-complete.xlsx. The goal is a credible VM inventory and readiness summary.',
  },
  {
    title: '2. VM Assignment',
    body: 'Assign in-scope VMs to target subnet, security group, storage, and wave buckets. Missing subnet or security placement should be fixed before export.',
  },
  {
    title: '3. Overrides And Remediation',
    body: 'Use VM Overrides for intentional profile, storage, or exclusion decisions. Use Remediation Backlog to track readiness blockers with owners and status.',
  },
  {
    title: '4. Image Import And Migration Ops',
    body: 'Image Import Planning tracks conversion/import readiness. Migration Ops combines wave, remediation, image, and planning state into cutover readiness.',
  },
  {
    title: '5. Network And Export',
    body: 'Review Network validation, then use Export Readiness to run preflight, preview Terraform files, download the readiness report, and build the handoff ZIP.',
  },
  {
    title: 'Tool Boundary',
    body: 'Carbon generates Terraform and handoff files. It does not run Terraform, import images, create IBM Cloud resources, or perform cutover.',
  },
];

export default function UserGuidePage() {
  return (
    <main className="user-guide-page">
      <header>
        <p className="eyebrow">Carbon user guide</p>
        <h1>RVTools to IBM Cloud VPC workflow guide</h1>
        <p className="user-guide-page__intro">
          Keep this window open while working through the migration planning
          workflow. Use each step to understand what the screen is for, what
          needs to be completed, and when to move on.
        </p>
      </header>
      <section className="user-guide-grid">
        {guideSections.map((section) => (
          <article key={section.title} className="user-guide-section">
            <h2>{section.title}</h2>
            <p>{section.body}</p>
          </article>
        ))}
      </section>
      <section className="user-guide-boundary">
        <h2>Reference Documents</h2>
        <p>
          The repository also includes docs/user-manual.md,
          docs/carbon-manual-uat-runbook.md, and
          docs/migration-handoff-package.md for deeper operator and UAT
          guidance.
        </p>
      </section>
    </main>
  );
}
