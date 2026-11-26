/**
 * DOM Utilities
 * Robust helper functions for interacting with modern frameworks (React, Vue, Angular)
 * and safely dispatching synthetic and native events.
 */

export class DomUtils {
  /**
   * Sets value on input elements while updating React/Vue internal state via prototype setter
   */
  public static setInputValue(el: HTMLInputElement | HTMLTextAreaElement, value: string): void {
    // Focus element
    el.focus();

    // Use native prototype value setter so React/Vue's valueTracker detects change
    const proto = el instanceof HTMLInputElement ? window.HTMLInputElement.prototype : window.HTMLTextAreaElement.prototype;
    const desc = Object.getOwnPropertyDescriptor(proto, 'value');

    if (desc && desc.set) {
      desc.set.call(el, value);
    } else {
      el.value = value;
    }

    // Dispatch native and synthetic events
    el.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
    el.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
    el.blur();
  }

  /**
   * Selects an option inside standard <select> elements
   */
  public static setSelectValue(select: HTMLSelectElement, optionTextOrValue: string): boolean {
    select.focus();
    const query = optionTextOrValue.toLowerCase().trim();
    let foundIndex = -1;

    for (let i = 0; i < select.options.length; i++) {
      const opt = select.options[i];
      if (opt.value.toLowerCase() === query || opt.text.toLowerCase().includes(query)) {
        foundIndex = i;
        break;
      }
    }

    if (foundIndex >= 0) {
      select.selectedIndex = foundIndex;
      select.dispatchEvent(new Event('change', { bubbles: true }));
      select.dispatchEvent(new Event('input', { bubbles: true }));
      select.blur();
      return true;
    }

    select.blur();
    return false;
  }

  /**
   * Toggles checkbox or radio button
   */
  public static setCheckboxValue(el: HTMLInputElement, checked: boolean): void {
    if (el.checked !== checked) {
      el.focus();
      el.click();
      el.checked = checked;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.blur();
    }
  }

  /**
   * Checks if an element is visible in the viewport
   */
  public static isVisible(el: HTMLElement): boolean {
    if (!el) return false;
    const doc = el.ownerDocument || document;
    const isJSDOM = typeof navigator !== 'undefined' && /jsdom|node/i.test(navigator.userAgent);
    
    // In headless test environments like JSDOM, offsetParent is always null
    if (isJSDOM) {
      const view = doc.defaultView || window;
      const style = view.getComputedStyle(el);
      return style.display !== 'none' && style.visibility !== 'hidden';
    }

    if (el.offsetParent === null) {
      const style = window.getComputedStyle(el);
      return style.position === 'fixed' && style.display !== 'none' && style.visibility !== 'hidden';
    }

    const style = window.getComputedStyle(el);
    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
  }

  /**
   * Clean text string (strips extra spaces, newlines, asterisks from required markers)
   */
  public static cleanText(text: string | null | undefined): string {
    if (!text) return '';
    return text.replace(/\s+/g, ' ').replace(/[*:]/g, '').trim();
  }

  /**
   * Attaches a File object to an input[type="file"] element via DataTransfer API
   */
  public static attachFileToInput(input: HTMLInputElement, file: File): boolean {
    try {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      input.files = dataTransfer.files;

      input.dispatchEvent(new Event('change', { bubbles: true }));
      input.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    } catch (err) {
      console.error('[DomUtils] Failed to attach file to input:', err);
      return false;
    }
  }
}
