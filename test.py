nums = [27, 0, 0, 0, 64, 127, 126, 0, 116, 101, 115, 116, 0, 0, 0, 0, 0, 7, 48, 46, 48, 0, 0, 0, 0, 4, 1, 49, 46, 48, 0, 126, 1, 105, 109, 117, 95, 104, 101, 97, 100, 105, 110, 103, 0, 1, 0, 0, 7, 111, 51, 53, 57, 46, 57, 57, 57, 56, 0, 0, 0, 0, 7, 123, 50, 46, 48, 0, 125]
buffer = bytearray(nums)

encoded_data = buffer.decode('ascii')
print(encoded_data)

print(max(nums))