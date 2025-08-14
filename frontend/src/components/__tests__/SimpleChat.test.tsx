import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SimpleChat from '../SimpleChat';
import { AuthProvider } from '../../contexts/AuthContext';
import * as api from '../../utils/api';

// Mock the API
jest.mock('../../utils/api');
const mockedLlmAPI = api.llmAPI as jest.Mocked<typeof api.llmAPI>;
const mockedDiaryAPI = api.diaryAPI as jest.Mocked<typeof api.diaryAPI>;

// Mock user for AuthContext
const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
};

const mockAuthContext = {
  user: mockUser,
  login: jest.fn(),
  logout: jest.fn(),
  isAuthenticated: true,
};

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AuthProvider value={mockAuthContext as any}>
    {children}
  </AuthProvider>
);

describe('SimpleChat Component (Casual Mode)', () => {
  const mockOnSwitchToGuided = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock successful API responses
    mockedLlmAPI.sendMessage.mockResolvedValue({
      success: true,
      response: 'Thank you for sharing! Tell me more about that.',
    });
    mockedDiaryAPI.generate.mockResolvedValue({
      success: true,
      diary: 'Today was a meaningful day filled with reflection.',
      entry_id: 1,
    });
  });

  test('renders Dear Me branding', () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    expect(screen.getByText('Dear Me')).toBeInTheDocument();
    expect(screen.getByText('Be Here, Be Now, Be You -- in a space you call your own')).toBeInTheDocument();
  });

  test('shows language selection dropdown', () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const languageSelect = screen.getByDisplayValue('English');
    expect(languageSelect).toBeInTheDocument();
    
    // Test language change
    fireEvent.change(languageSelect, { target: { value: 'zh' } });
    expect(languageSelect).toHaveValue('zh');
  });

  test('shows AI model selection dropdown', () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const modelSelect = screen.getByDisplayValue('Gemma 3 (4B)');
    expect(modelSelect).toBeInTheDocument();
    
    // Test model change
    fireEvent.change(modelSelect, { target: { value: 'qwen3:8b' } });
    expect(modelSelect).toHaveValue('qwen3:8b');
  });

  test('shows Try Guided Mode button', () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const guidedModeButton = screen.getByText('Try Guided Mode');
    expect(guidedModeButton).toBeInTheDocument();
    
    // Test clicking the button
    fireEvent.click(guidedModeButton);
    expect(mockOnSwitchToGuided).toHaveBeenCalled();
  });

  test('allows sending messages in free-form conversation', async () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    // Type a message
    fireEvent.change(messageInput, { target: { value: 'Hello, how are you today?' } });
    expect(messageInput).toHaveValue('Hello, how are you today?');

    // Send the message
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockedLlmAPI.sendMessage).toHaveBeenCalledWith(
        'Hello, how are you today?',
        [],
        'en',
        'gemma3:4b'
      );
    });

    // Check that the response appears
    await waitFor(() => {
      expect(screen.getByText('Thank you for sharing! Tell me more about that.')).toBeInTheDocument();
    });

    // Input should be cleared
    expect(messageInput).toHaveValue('');
  });

  test('handles Enter key to send message', async () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    
    // Type a message and press Enter
    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    fireEvent.keyPress(messageInput, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(mockedLlmAPI.sendMessage).toHaveBeenCalledWith(
        'Test message',
        [],
        'en',
        'gemma3:4b'
      );
    });
  });

  test('disables send button when input is empty', () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const sendButton = screen.getByText('Send');
    expect(sendButton).toBeDisabled();

    const messageInput = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(messageInput, { target: { value: 'Some text' } });
    expect(sendButton).not.toBeDisabled();

    fireEvent.change(messageInput, { target: { value: '' } });
    expect(sendButton).toBeDisabled();
  });

  test('shows loading state while sending message', async () => {
    // Make API call take longer
    mockedLlmAPI.sendMessage.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        success: true,
        response: 'Response after delay',
      }), 100))
    );

    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    // Should show thinking indicator
    expect(screen.getByText('Thinking...')).toBeInTheDocument();
    
    // Input should be disabled
    expect(messageInput).toBeDisabled();

    await waitFor(() => {
      expect(screen.getByText('Response after delay')).toBeInTheDocument();
    });

    // Loading should be gone
    expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
    expect(messageInput).not.toBeDisabled();
  });

  test('builds conversation history correctly', async () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    // Send first message
    fireEvent.change(messageInput, { target: { value: 'First message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockedLlmAPI.sendMessage).toHaveBeenCalledWith(
        'First message',
        [],
        'en',
        'gemma3:4b'
      );
    });

    // Send second message
    fireEvent.change(messageInput, { target: { value: 'Second message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      // Second call should include conversation history
      const secondCall = mockedLlmAPI.sendMessage.mock.calls[1];
      expect(secondCall[0]).toBe('Second message');
      expect(secondCall[1]).toHaveLength(2); // Should have 2 previous messages
    });
  });

  test('offers diary generation after several exchanges', async () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    // Send 5 messages to trigger diary offer
    for (let i = 1; i <= 5; i++) {
      fireEvent.change(messageInput, { target: { value: `Message ${i}` } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText('Thank you for sharing! Tell me more about that.')).toBeInTheDocument();
      });
    }

    // Should show diary generation prompt
    await waitFor(() => {
      expect(screen.getByText(/Would you like me to create a personal diary entry/)).toBeInTheDocument();
    });
  });

  test('generates diary when user agrees', async () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    // Trigger diary offer by having several exchanges
    for (let i = 1; i <= 5; i++) {
      fireEvent.change(messageInput, { target: { value: `Message ${i}` } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText('Thank you for sharing! Tell me more about that.')).toBeInTheDocument();
      });
    }

    // User says yes to diary
    fireEvent.change(messageInput, { target: { value: 'Yes, create a diary' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockedDiaryAPI.generate).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('Today was a meaningful day filled with reflection.')).toBeInTheDocument();
    });
  });

  test('handles Chinese language properly', () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    // Change to Chinese
    const languageSelect = screen.getByDisplayValue('English');
    fireEvent.change(languageSelect, { target: { value: 'zh' } });

    // Check Chinese text appears
    expect(screen.getByText('中文')).toBeInTheDocument();
    expect(screen.getByText('尝试引导模式')).toBeInTheDocument();
    
    // Chinese placeholder should appear
    expect(screen.getByPlaceholderText('输入你的消息...')).toBeInTheDocument();
  });

  test('text is properly aligned to the left', () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    // Send a message to create a message bubble
    fireEvent.change(messageInput, { target: { value: 'Test message alignment' } });
    fireEvent.click(sendButton);

    // Check that messages appear with proper alignment
    expect(screen.getByText('Test message alignment')).toBeInTheDocument();
  });

  test('shows user info and logout button', () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    expect(screen.getByText('testuser')).toBeInTheDocument();
    
    const logoutButton = screen.getByText('Logout');
    expect(logoutButton).toBeInTheDocument();
    
    fireEvent.click(logoutButton);
    expect(mockAuthContext.logout).toHaveBeenCalled();
  });

  test('handles API errors gracefully', async () => {
    // Mock API error
    mockedLlmAPI.sendMessage.mockRejectedValue(new Error('Network error'));

    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Sorry, something went wrong/)).toBeInTheDocument();
    });
  });

  test('model selection affects API calls', async () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    // Change model
    const modelSelect = screen.getByDisplayValue('Gemma 3 (4B)');
    fireEvent.change(modelSelect, { target: { value: 'qwen3:8b' } });

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(messageInput, { target: { value: 'Test with Qwen' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockedLlmAPI.sendMessage).toHaveBeenCalledWith(
        'Test with Qwen',
        [],
        'en',
        'qwen3:8b'  // Should use the selected model
      );
    });
  });

  test('maintains conversation context across model changes', async () => {
    render(
      <TestWrapper>
        <SimpleChat onSwitchToGuided={mockOnSwitchToGuided} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    // Send first message with default model
    fireEvent.change(messageInput, { target: { value: 'First message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockedLlmAPI.sendMessage).toHaveBeenCalledWith(
        'First message',
        [],
        'en',
        'gemma3:4b'
      );
    });

    // Change model
    const modelSelect = screen.getByDisplayValue('Gemma 3 (4B)');
    fireEvent.change(modelSelect, { target: { value: 'qwen3:8b' } });

    // Send second message with new model
    fireEvent.change(messageInput, { target: { value: 'Second message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      const secondCall = mockedLlmAPI.sendMessage.mock.calls[1];
      expect(secondCall[0]).toBe('Second message');
      expect(secondCall[1]).toHaveLength(2); // Should still have conversation history
      expect(secondCall[3]).toBe('qwen3:8b'); // Should use new model
    });
  });
});