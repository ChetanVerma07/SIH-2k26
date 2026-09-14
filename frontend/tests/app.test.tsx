import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../src/App';
import { AnalysisProvider } from '../src/hooks/useAnalysisContext';
import Materials from '../src/pages/Materials';
import Climate from '../src/pages/Climate';
import NewAnalysis from '../src/pages/NewAnalysis';

function renderApp(initialRoute = '/') {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <AnalysisProvider>
        <App />
      </AnalysisProvider>
    </MemoryRouter>
  );
}

describe('Navigation', () => {
  it('renders the dashboard by default', () => {
    renderApp('/');
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
  });

  it('navigates to New Analysis via sidebar', () => {
    renderApp('/');
    const links = screen.getAllByRole('link', { name: /new analysis/i });
    fireEvent.click(links[0]);
    expect(screen.getByRole('heading', { name: /new analysis/i })).toBeInTheDocument();
  });

  it('navigates to Materials page', async () => {
    renderApp('/');
    const materialsLink = screen.getByText('Materials');
    fireEvent.click(materialsLink);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /materials/i })).toBeInTheDocument();
    });
  });
});

describe('Materials page', () => {
  it('renders material rows and filters by search', async () => {
    render(
      <MemoryRouter>
        <AnalysisProvider>
          <Materials />
        </AnalysisProvider>
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText(/rammed earth/i)).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/search materials/i), { target: { value: 'straw' } });
    expect(screen.getByText(/straw bale/i)).toBeInTheDocument();
    expect(screen.queryByText(/rammed earth/i)).not.toBeInTheDocument();
  });
});

describe('Climate selection', () => {
  it('switches climate preset and shows updated location', async () => {
    render(
      <MemoryRouter>
        <AnalysisProvider>
          <Climate />
        </AnalysisProvider>
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText(/Leh, Ladakh/i)).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/select climate preset/i), { target: { value: 'hot-dry' } });
    await waitFor(() => expect(screen.getByText(/Jaisalmer/i)).toBeInTheDocument());
  });
});

describe('New Analysis form validation', () => {
  it('shows validation errors when required fields are invalid', async () => {
    render(
      <MemoryRouter>
        <AnalysisProvider>
          <NewAnalysis />
        </AnalysisProvider>
      </MemoryRouter>
    );
    const nameInput = screen.getByLabelText(/analysis name/i);
    fireEvent.change(nameInput, { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: /run analysis/i }));
    await waitFor(() =>
      expect(screen.getByText(/please fix the following/i)).toBeInTheDocument()
    );
  });
});

describe('Design configuration', () => {
  it('toggles between auto optimize and manual design modes', () => {
    render(
      <MemoryRouter>
        <AnalysisProvider>
          <NewAnalysis />
        </AnalysisProvider>
      </MemoryRouter>
    );
    const manualButton = screen.getByRole('button', { name: /manual design/i });
    fireEvent.click(manualButton);
    expect(screen.getByText(/Length/i)).toBeInTheDocument();
  });
});
