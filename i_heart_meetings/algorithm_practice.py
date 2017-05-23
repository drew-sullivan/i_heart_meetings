vowels = ['a', 'e', 'i', 'o', 'u', 'y']
count = 0
sample_str = "the dog went to the store to get a bone. He was very hungry."
new_str = ''
frequency = {}
for letter in sample_str:
    if letter not in vowels:
        new_str += letter
    else:
        if letter in frequency.keys():
            frequency[letter] += 1
        else:
            frequency[letter] = 1
        count += 1
backwards_str = sample_str[::-1]
most_used_vowel = max(frequency, key=frequency.get)

print('Backwards String: {0}'.format(backwards_str))
print('New String: {0}'.format(new_str))
print('Num vowels: {0}'.format(count))
print('Most used vowel: {0}'.format(most_used_vowel))
print('String as a list: {0}'.format(sample_str.split()))
