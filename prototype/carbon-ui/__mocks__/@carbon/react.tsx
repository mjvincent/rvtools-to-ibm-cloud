// Mock for @carbon/react — provides simple HTML stubs for all used components
import React from 'react';

export const Button = ({ children, onClick, disabled, kind, size, renderIcon: Icon, ...rest }: any) => (
  <button onClick={onClick} disabled={disabled} data-kind={kind} data-size={size} {...rest}>
    {Icon && <Icon />}
    {children}
  </button>
);

export const Checkbox = ({ id, labelText, checked, onChange, hideLabel, ...rest }: any) => (
  <input
    type="checkbox"
    id={id}
    aria-label={labelText}
    checked={checked}
    onChange={(e) => onChange(e, { checked: e.target.checked })}
    {...rest}
  />
);

export const Column = ({ children, ...rest }: any) => <div {...rest}>{children}</div>;

export const Content = ({ children, className }: any) => <main className={className}>{children}</main>;

export const FileUploaderDropContainer = ({ labelText, onAddFiles, accept }: any) => (
  <div
    data-testid="file-drop"
    onClick={() => {}}
    onDrop={(e) => {
      const files = Array.from((e.dataTransfer?.files as FileList) || []);
      if (files.length) onAddFiles(e, { addedFiles: files });
    }}
  >
    {labelText}
    <input
      type="file"
      accept={accept?.join(',')}
      data-testid="file-input"
      onChange={(e) => {
        const files = Array.from(e.target.files || []);
        if (files.length) onAddFiles(e, { addedFiles: files });
      }}
    />
  </div>
);

export const Grid = ({ children, fullWidth, className }: any) => <div className={className}>{children}</div>;

export const Header = ({ children, 'aria-label': ariaLabel }: any) => (
  <header aria-label={ariaLabel}>{children}</header>
);

export const HeaderGlobalAction = ({ children, onClick, 'aria-label': ariaLabel }: any) => (
  <button onClick={onClick} aria-label={ariaLabel}>{children}</button>
);

export const HeaderGlobalBar = ({ children }: any) => <div>{children}</div>;

export const HeaderName = ({ children, href, prefix }: any) => (
  <a href={href}>{prefix} {children}</a>
);

export const HeaderPanel = ({ children, expanded, 'aria-label': ariaLabel }: any) => (
  expanded ? <div aria-label={ariaLabel}>{children}</div> : null
);

export const InlineNotification = ({ kind, title, subtitle, onCloseButtonClick, lowContrast }: any) => (
  <div role="alert" data-kind={kind}>
    <strong>{title}</strong>
    {subtitle && <span>{subtitle}</span>}
    {onCloseButtonClick && <button onClick={onCloseButtonClick} aria-label="close">×</button>}
  </div>
);

export const Layer = ({ children, className }: any) => <div className={className}>{children}</div>;

export const Modal = ({ open, children, modalHeading, primaryButtonText, secondaryButtonText, onRequestClose, onRequestSubmit }: any) => {
  if (!open) return null;
  return (
    <div role="dialog" aria-modal="true">
      <h2>{modalHeading}</h2>
      {children}
      <button onClick={onRequestSubmit}>{primaryButtonText}</button>
      <button onClick={onRequestClose}>{secondaryButtonText}</button>
    </div>
  );
};

export const Search = ({ id, labelText, placeholder, value, onChange }: any) => (
  <input
    id={id}
    type="search"
    aria-label={labelText}
    placeholder={placeholder}
    value={value}
    onChange={onChange}
  />
);

export const Select = ({ id, labelText, value, onChange, children }: any) => (
  <div>
    <label htmlFor={id}>{labelText}</label>
    <select id={id} value={value} onChange={onChange}>{children}</select>
  </div>
);

export const SelectItem = ({ value, text }: any) => <option value={value}>{text}</option>;

export const SideNav = ({ children, 'aria-label': ariaLabel, expanded, isPersistent }: any) => (
  <nav aria-label={ariaLabel}>{children}</nav>
);

export const SideNavItems = ({ children }: any) => <ul>{children}</ul>;

export const SideNavLink = ({ children, renderIcon: Icon, href, isActive, onClick }: any) => (
  <li>
    <a href={href} onClick={onClick} aria-current={isActive ? 'page' : undefined}>
      {Icon && <Icon />}
      {children}
    </a>
  </li>
);

export const Tag = ({ children, type, ...rest }: any) => (
  <span data-type={type} data-testid="carbon-tag" {...rest}>{children}</span>
);

export const TextArea = ({ id, labelText, value, onChange }: any) => (
  <div>
    <label htmlFor={id}>{labelText}</label>
    <textarea id={id} value={value} onChange={onChange} />
  </div>
);

export const TextInput = ({ id, labelText, value, onChange }: any) => (
  <div>
    <label htmlFor={id}>{labelText}</label>
    <input id={id} type="text" value={value} onChange={onChange} />
  </div>
);

export const Tile = ({ children, className, onClick, ...rest }: any) => (
  <div className={className} onClick={onClick} data-testid="tile" {...rest}>{children}</div>
);

export const InlineLoading = ({ description }: any) => <span data-testid="inline-loading">{description}</span>;
