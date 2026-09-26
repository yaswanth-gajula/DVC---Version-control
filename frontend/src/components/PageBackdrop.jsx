export default function PageBackdrop({ variant = "default" }) {
  return (
    <div className={`page-backdrop page-backdrop-${variant}`} aria-hidden="true">
      <span className="backdrop-orbit backdrop-orbit-one" />
      <span className="backdrop-orbit backdrop-orbit-two" />
      <span className="backdrop-node backdrop-node-one" />
      <span className="backdrop-node backdrop-node-two" />
      <span className="backdrop-node backdrop-node-three" />
    </div>
  );
}
