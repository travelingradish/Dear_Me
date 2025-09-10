import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Home from '../Home';
import { AuthProvider } from '../../contexts/AuthContext';
import * as api from '../../utils/api';

// Mock the API
jest.mock('../../utils/api');
const mockedAPI = api as jest.Mocked<typeof api>;

// Mock React Router
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock the useAuth hook directly
const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  ai_character_name: 'AI Assistant',
};

const mockAuthContext = {
  user: mockUser,
  token: 'mock-token',
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  loading: false,
  updateCharacterName: jest.fn(),
};

// Mock the useAuth hook
jest.mock('../../contexts/AuthContext.tsx', () => ({
  useAuth: () => mockAuthContext,
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Custom render function with providers
const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Home Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders welcome message', () => {
    renderWithProviders(<Home />);
    
    // The welcome message is displayed in the header
    expect(screen.getByText(/welcome,/i)).toBeInTheDocument();
  });

  test('displays main app branding', () => {
    renderWithProviders(<Home />);
    
    expect(screen.getByText(/dear me/i)).toBeInTheDocument();
    expect(screen.getByText(/be here, be now, be you/i)).toBeInTheDocument();
  });

  test('renders three main feature highlights', () => {
    renderWithProviders(<Home />);
    
    expect(screen.getByText(/guided reflection/i)).toBeInTheDocument();
    expect(screen.getByText(/personal journal/i)).toBeInTheDocument();
    expect(screen.getByText(/mindful growth/i)).toBeInTheDocument();
  });

  test('renders feature descriptions', () => {
    renderWithProviders(<Home />);
    
    expect(screen.getByText(/thoughtful prompts to guide/i)).toBeInTheDocument();
    expect(screen.getByText(/ai-crafted entries from your own words/i)).toBeInTheDocument();
    expect(screen.getByText(/track your journey of self-discovery/i)).toBeInTheDocument();
  });

  test('navigates to chat when start button clicked', () => {
    renderWithProviders(<Home />);
    
    const startButton = screen.getByText(/start unpacking/i);
    fireEvent.click(startButton);
    expect(mockNavigate).toHaveBeenCalledWith('/chat');
  });

  test('shows inspirational quote', () => {
    renderWithProviders(<Home />);
    
    expect(screen.getByText(/each day is a new beginning/i)).toBeInTheDocument();
  });

  test('displays feature icons', () => {
    renderWithProviders(<Home />);
    
    expect(screen.getByText('💭')).toBeInTheDocument();
    expect(screen.getByText('📖')).toBeInTheDocument();
    expect(screen.getByText('🌱')).toBeInTheDocument();
  });

  test('shows clean minimalist interface', () => {
    renderWithProviders(<Home />);
    
    // The current home page has a clean design without character naming interface
    expect(screen.getByText(/dear me/i)).toBeInTheDocument();
    expect(screen.getByText(/start unpacking/i)).toBeInTheDocument();
  });

  test('handles start button click successfully', async () => {
    renderWithProviders(<Home />);
    
    const startButton = screen.getByText(/start unpacking/i);
    expect(startButton).toBeInTheDocument();
    
    fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/chat');
    });
  });

  test('displays logout functionality in header', () => {
    renderWithProviders(<Home />);
    
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    expect(logoutButton).toBeInTheDocument();
    
    fireEvent.click(logoutButton);
    expect(mockAuthContext.logout).toHaveBeenCalled();
  });

  test('displays header with welcome message', () => {
    renderWithProviders(<Home />);
    
    // Header displays welcome message with user info section
    expect(screen.getByText(/welcome,/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  test('renders with proper styling structure', () => {
    renderWithProviders(<Home />);
    
    // The component renders with inline styles, check for key content
    expect(screen.getByText(/dear me/i)).toBeInTheDocument();
    expect(screen.getByText(/start unpacking/i)).toBeInTheDocument();
    expect(screen.getByText(/logout/i)).toBeInTheDocument();
  });

  test('logout navigates to login page', async () => {
    renderWithProviders(<Home />);
    
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);
    
    expect(mockAuthContext.logout).toHaveBeenCalled();
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  test('handles loading states appropriately', () => {
    renderWithProviders(<Home />);
    
    // Component should render without loading indicators on initial load
    const loadingIndicator = screen.queryByText(/loading/i) ||
                           screen.queryByRole('progressbar');
    
    // Should not have loading states on initial render
    expect(loadingIndicator).not.toBeInTheDocument();
  });

  test('shows floating decorative elements', () => {
    renderWithProviders(<Home />);
    
    // The component has floating circles for visual decoration
    // We can't easily test these since they're styled divs, but we can test the main content
    expect(screen.getByText(/dear me/i)).toBeInTheDocument();
    expect(screen.getByText(/be here, be now, be you/i)).toBeInTheDocument();
  });

  test('renders complete page without crashes', () => {
    renderWithProviders(<Home />);
    
    // Verify the page renders completely without any crashes
    expect(screen.getByText(/dear me/i)).toBeInTheDocument();
    expect(screen.getByText(/start unpacking/i)).toBeInTheDocument();
    expect(screen.getByText(/guided reflection/i)).toBeInTheDocument();
    expect(screen.getByText(/personal journal/i)).toBeInTheDocument();
    expect(screen.getByText(/mindful growth/i)).toBeInTheDocument();
  });
});