export default function Button({ 
  children, 
  onClick, 
  disabled = false, 
  variant = "primary",
  className = "" 
}) {
  const baseClasses = "px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900";
  
  const variantClasses = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500",
    danger: "bg-red-600 hover:bg-red-700 text-white focus:ring-red-500",
    secondary: "bg-gray-600 hover:bg-gray-700 text-white focus:ring-gray-500"
  };
  
  const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";
  
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${disabledClasses} ${className}`}
    >
      {children}
    </button>
  );
}
