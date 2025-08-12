export default function Card({ title, children }) {
  return (
    <div className="bg-gray-900 rounded-lg p-6 shadow-lg border border-gray-700">
      {title && (
        <h2 className="text-xl font-semibold text-white mb-4">{title}</h2>
      )}
      {children}
    </div>
  );
}
