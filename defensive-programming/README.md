# Defensive Programming

In distributed systems, errors can occur due to bugs, malicious input and unexpected data. 
Defensive techniques ensure that the system remains correct and resilient.

# System Design

## Concepts

- Correctness: Code should meet its specifications under all valid inputs.
- Complexity: Keep algorithms efficient and simple.
- Flexibility: Write modular, reusable components that can evolve.
  - Weak Coupling: Modules should have minimal dependencies on each other,
    meaning one module knows as little as possible about the implementation details of others.
    Achieved by relying on interfaces instead of concrete classes. (צמידות)
  - Strong Cohesion: Elements within a module (like a class or function) are tightly related,
    logically connected, and focused on a single, well-defined purpose. (לכידות)
- Use Cases: Define concrete user stories to clarify expected behavior.

## User Stories

Use cases and user stories describe what the user wants to do and why,
helping designers and developers understand functional requirements and user behavior.

## UML (Unified Modeling Language)

Standardized visual language used to model, design, and document software systems.

It has multiple relationship types.

### 1. Association (→)

- Meaning: A general relationship where one class uses or knows another.
- Multiplicity: 1-to-1, 1-to-many, or many-to-many.
- Example: `User` 0..\* → 1 `Account` (“A user has one or more accounts.”)

### 2. Inheritance (⇑)

- Meaning: A subclass inherits attributes and methods from a parent class.
- Example: `Admin` -> (arrow with dark head) `User` (“Admin is a specialized kind of User.”)

### 3. Implementation (– – – >)

- Meaning: A class implements the behavior defined by an interface.
- Example: `AuthService` – – – > `IAuthenticable`

## Data Flow Diagram

Visual representation of how data moves through a system.
It shows where data comes from, where it goes, and how it’s transformed.

```
[User] --> (Login Process) --> [Database]
```

## Example

### User Stories

1. “As a user, I can register and log in to access my profile.”
2. “As an admin, I can view and manage users.”
3. “The system stores users and login data securely.”

### Identified Classes

| Class       | Responsibility                                     |
| ----------- | -------------------------------------------------- |
| User        | Stores user information like username and password |
| Admin       | Inherits from User, adds admin-specific privileges |
| Account     | Represents user’s profile or data                  |
| AuthService | Handles registration and login logic               |
| Database    | Stores Users and Accounts                          |

### Relationships

- `Admin` inherits from `User`
- `User` has an `Account`
- `AuthService` uses `Database`
- `Database` stores many `Users`
- `AuthService` authenticates a `User`

```plaintext
             +-------------------+
             |     User          |
             +-------------------+
             | - username        |
             | - passwordHash    |
             +-------------------+
             | + login()         |
             | + logout()        |
             +-------------------+
                     ▲
                     │ Inherits
                     │
             +-------------------+
             |     Admin         |
             +-------------------+
             | + manageUsers()   |
             +-------------------+

             +-------------------+
             |     Account       |
             +-------------------+
             | - id              |
             | - data            |
             +-------------------+

User 1 ──── 1 Account
(User has one Account)

             +-------------------+
             |   AuthService     |
             +-------------------+
             | + registerUser()  |
             | + loginUser()     |
             +-------------------+
                     │
             Dependency ──→ Database

             +-------------------+
             |     Database      |
             +-------------------+
             | + saveUser()      |
             | + getUser()       |
             +-------------------+
```

---

# Object-Oriented Programming (OOP)

A programming model where software is organized around data, or "objects", rather than functions and logic.

After we design the general structure of a system we delve into each object / entity and the services it supplies for other entities.

### Core Concepts

- Class: Blueprint for objects.
- Object: Instance of a class.
- Encapsulation: Hide internal state behind public methods.
- Inheritance: Reuse and extend base functionality.
- Polymorphism: Common interface, different implementations.

### Code Example

- Scopes: Public (`+`), Private (`-`) and Protected (`#`).
- Abstract base class `Shape`.
- Derived `Circle` overriding `area()`.
- Use of virtual destructor.
- Polymorphism through base pointer.
- Note: calling virtual functions in ctor does not work as expected, original function will be called.
- By default, `class` fields are `private` (for encapsulation) and `struct` fields are `public` (to ensure compatbility with C).

```cpp
class Shape {
public:
  // Abstract method
    virtual double area() const = 0; 
    virtual ~Shape() = default;
};

class Circle : public Shape {
private:
    double radius;
public:
    Circle(double r): radius(r) {}
    double area() const override { return 3.1415 * radius * radius; }
};

int main() {
    // Polymorphism
    Shape* shape = new Circle(5.0);   
    std::cout << "Area: " << shape->area() << std::endl;
    delete shape;                     
    return 0;
}
```

---

# C++ (Cpp)

## Basics

Cpp is a compiled language that combines low-level memory control with high-level abstractions.

It has no garbage collector, so it is up to the user to plan objects destruction and memory cleanup.

```cpp
#include <iostream>
#include <string>
#include <cstdint>
#include <algorithm>

int add(int a, int b) {
    return a + b;
}

int main() {
    // Well-defined number types.
    uint8_t age = 25;
    uint32_t salary = 100000;
    uint32_t max = std::max(1,3);
    uint32_t min = std::min(1,3);

    // I/O
    std::cout << "Age: " << age << std::endl;
    std::cout << "Salary: " << salary << std::endl;

    std::string name;
    std::cout << "Enter your name: ";
    std::cin >> name;
    // Also valid: std::getline(std::cin, name);
    std::cout << "Hello, " << name << "!" << std::endl;
    // Get line from stdin with max length:
    int max_length = 1024;
    char data[max_length];
    std::cin.getline(data, max_length);

    // foreach
    std::vector<int> nums = {1, 2, 3, 4, 5};
    for (int value : nums) {
        std::cout << value << " ";
    }
    std::cout << std::endl;

    // strings
    std::string text = "hello world";
    // length()
    std::cout << "Length: " << text.length() << std::endl;
    // substr()
    std::string sub = text.substr(0, 5); // "hello"
    // find()
    size_t pos = text.find("world");
    if (pos != std::string::npos) {
        std::cout << "'world' found at position " << pos << std::endl;
    }

    // numbers <--> strings
    int num = 42;
    std::string str = std::to_string(num);

    std::string text = "123";
    int n = std::stoi(text);
    double d = std::stod("3.14");

    // Function pointer
    int (*fp)(int,int) = &add;
}
```

---

## Cpp Runtime Memory Layout — Stack, Heap, Code, and Growth Direction

When a Cpp program runs, memory is divided into regions:

| Region                  | Purpose                                                         | Example                                         |
| ----------------------- | --------------------------------------------------------------- | ----------------------------------------------- |
| Code / Text Segment     | Stores compiled instructions (functions).                       | `main()` machine code lives here.               |
| Static / Global Segment | Stores global and static variables.                             | `static int counter = 0;`                       |
| Heap                    | Dynamically allocated memory (`new`, `malloc`, smart pointers). | `int* p = new int(10);`                         |
| Stack                   | Function calls, local variables, return addresses.              | Inside `main()`, local `int x = 5;` lives here. |

### Growth Direction

- Stack grows downward (toward lower memory addresses).
- Heap grows upward (toward higher addresses).
  They expand toward each other. Memory collision = stack/heap overflow.

```
| high addresses |
+----------------+
|   Stack (↓)    |
|----------------|
|      ...       |
|----------------|
|   Heap (↑)     |
+----------------+
| low addresses  |
```

### Stack

- Calling convention - how functions pass parameters
  - cdecl - caller cleans stack, used in c/cpp.
  - stdcall - function cleans stack, used in WinAPI.
- Stack Frame - return address, parameters, local variables, registers backup
- ESP - register that stores current location on the stack, changes with push/pop.
- EBP - points to current stack frame.

## Endianness

Little Endian means the least significant byte (LSB) is stored first (at the lowest address).

Example:

```cpp
int x = 0x12345678;
```

Memory layout (addresses increasing →):

```
78 56 34 12
```

Big Endian would store:

```
12 34 56 78
```

Most modern PCs (x86, ARM) are Little Endian.

---

## Manual Memory Management - `new` / `delete`

```cpp
#include <iostream>

int main() {
    int* num = new int(42); // allocate memory
    std::cout << "Value: " << *num << std::endl;

    *num = 100;             // modify value
    std::cout << "New Value: " << *num << std::endl;

    delete num;             // free memory
    num = nullptr;          // avoid dangling pointer

    Dog* d = new Dog(); // create object on heap
    d->bark();
    delete d;           // must delete manually

    return 0;
}
```

---

## References, Move, and Smart Pointers

| Term                             | Definition                                                                                                                   | Example                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| lvalue reference (`T&`)          | Refers to an existing object (has address).                                                                                  | `int x = 5; int& r = x;`             |
| rvalue reference (`T&&`)         | Refers to a temporary or movable value. Used for move semantics.                                                             | `int&& temp = 10;`                   |
| `std::move`                      | Casts an lvalue to an rvalue reference, allowing resources to be moved.                                                      | `vec2 = std::move(vec1);`            |
| Smart pointer vs Regular pointer | Smart pointers manage memory automatically; raw pointers require manual `delete` - Shouldn't be used together to avoid bugs. | `new/delete` vs `std::unique_ptr`    |
| `std::unique_ptr`                | Smart pointer that owns an object exclusively (no copies). Automatically deletes when out of scope.                          | `auto p = std::make_unique<int>(5);` |
| `std::shared_ptr`                | Smart pointer that uses reference counting; multiple owners.                                                                 | `auto p = std::make_shared<int>(5);` |

### `std::unique_ptr` Example

```cpp
#include <memory>
#include <iostream>

struct Node {
    int value;
    Node(int v): value(v) {}
};

int main() {
    std::unique_ptr<Node> ptr = std::make_unique<Node>(42);
    std::cout << ptr->value << std::endl;
    // In order to pass value - pointer must be moved.
    // From now on ptr can't be used - points to nothing.
    std::unique_ptr<Node> ptr2 = std::move(ptr);
    std::cout << ptr2->value << std::endl;

    // Can also be given a "raw" pointer.
    std::unique_ptr<Node> ptr2(new Node(43));
}
```

### `std::shared_ptr` Example

```cpp
#include <memory>
#include <iostream>

struct Resource {
    ~Resource() { std::cout << "Freed\n"; }
};

int main() {
    std::shared_ptr<Resource> r1 = std::make_shared<Resource>();
    std::shared_ptr<Resource> r2 = r1;
    std::cout << "Use count: " << r1.use_count() << std::endl;
}
```

---

## Classes

- `const` function - means that object properties cannot be changed.
  `const` reference to object - only `const` functions can be used.
- Use public inheritence because then your users can use the public members of the mother class.
- Copy ctor and operator= are available by default and perform shallow copy, implictly deleted if any member is non-copyable.

```cpp
#include <iostream>
#include <cstring>
#include <string>

// ---------------- Base Abstract Class ----------------
class Printable {
public:
    // Abstract method (pure virtual)
    virtual void print() const = 0;
    virtual ~Printable() = default;
};

// ---------------- Buffer Class ----------------
class Buffer : public Printable {
private:
    char* data;
    size_t size;

    // Private functions
    void _allocate(const char* str) {
        size = std::strlen(str);
        data = new char[size + 1];
        std::strcpy(data, str);
    }

public:
    // Constructors - Rule of 5
    // Regular (not counted)
    Buffer(const char* str) { _allocate(str); }
    // Copy
    Buffer(const Buffer& other) { _allocate(other.data); }
    // Operator=
    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            delete[] data;
            _allocate(other.data);
        }
        return *this;
    }
    // Move
    Buffer(Buffer&& other) : data(other.data), size(other.size) {
        other.data = nullptr;
        other.size = 0;
    }
    // Move operator=
    Buffer& operator=(Buffer&& other) {
        if (this != &other) {
            delete[] data;
            data = other.data;
            size = other.size;
            other.data = nullptr;
            other.size = 0;
        }
        return *this;
    }
    // Virtual destructor
    ~Buffer() override { delete[] data; }

    // Method overloading
    void print() const override { std::cout << data << std::endl; }
    void print(const std::string& prefix) const { std::cout << prefix << data << std::endl; }

    // Public functions
    const char* c_str() const { return data; }
    size_t length() const { return size; }

    // Friend operators
    friend std::ostream& operator<<(std::ostream& stream, const Buffer& buf) {
        return stream << buf.data;
    }

    friend Buffer operator*(int times, const Buffer& buf) {
        std::string s;
        for (int i = 0; i < times; ++i)
            s += buf.data;
        return Buffer(s.c_str());
    }
};

// ---------------- Derived Class ----------------
class UpperBuffer : public Buffer {
public:
    // Constructors...
    UpperBuffer(const char* str) : Buffer(str) {}

    void print() const override {
        std::string temp = c_str();
        for (char& c : temp)
            c = std::toupper(c);
        std::cout << temp << std::endl;
    }
};

// ---------------- Usage ----------------
int main() {
    std::cout << "=== Base buffer ===\n";
    Buffer b1("Hello");
    b1.print();

    std::cout << "\n=== Prefix print ===\n";
    b1.print("Prefix: ");

    std::cout << "\n=== Operator * ===\n";
    Buffer b2 = 3 * b1;
    std::cout << b2 << std::endl;

    std::cout << "\n=== Derived class ===\n";
    UpperBuffer ub("hello world");
    ub.print();  // prints uppercase

    return 0;
}
```

## VTABLE — Virtual Function Table

A vtable (virtual table) is a hidden mechanism that Cpp uses to implement runtime polymorphism for classes with virtual functions.

When a class has at least one `virtual` function:

- The compiler generates a vtable — a table of function pointers.
- Each object of that class stores a hidden pointer (`vptr`) to its class’s vtable.
- At runtime, the correct function is called through that table, based on the actual type of the object (not the pointer type).
- The vtable is essentially an array of pointers to functions and is located at offset 0 of the object's memory.

### Example

```cpp
#include <iostream>

class Base {
public:
    virtual void speak() const { std::cout << "Base speaks\n"; }
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    void speak() const override { std::cout << "Derived speaks\n"; }
};

int main() {
    Base* obj = new Derived();
    obj->speak(); // dynamically calls Derived::speak via vtable
    delete obj;
}
```

Output: `Derived speaks`

If there were no `virtual` functions, it would instead call `Base::speak()` (static binding).
So the vtable enables dynamic dispatch.

In memory, the 4 bytes at `*obj` are the pointer to `Derived::speak()`.

If there were more functions their pointers would be at `*(obj + 4)`, `*(obj + 8)`, etc (assuming 32 bit architecture).

## Excptions

- Throwing copies the object to the exception object, Unwinding (finding `catch` handler) destroys the local object.
- After the handler finishes, the thrown exception object is destroyed

```cpp
#include <iostream>
#include <exception>
#include <string>

// Custom exception
class MyException : public std::exception {
private:
    std::string message;
public:
    MyException(const std::string& msg) : message(msg) {}

    const char* what() const override {
        return message.c_str();
    }
};

int main() {
    try {
        std::cout << "Starting program..." << std::endl;

        int scenario = 0;
        std::cin >> scenario;

        if (scenario == 1)
            throw MyException("custom");
        else if (scenario == 2)
            throw std::runtime_error("runtime");
        else if (scenario == 3)
            throw std::exception("generic");
        else if (scenario == 4)
            // This runs but please don't do it.
            throw 1;

        std::cout << "Program finished normally." << std::endl;
    }
    catch (const MyException& e) {
        std::cerr << "[MyException caught] " << e.what() << std::endl;
    }
    catch (const std::runtime_error& e) {
        std::cerr << "[std::runtime_error caught] " << e.what() << std::endl;
    }
    catch (...) {
        std::cerr << "[Unknown exception caught]" << std::endl;
    }

    std::cout << "Program continues after catch." << std::endl;
    return 0;
}
```

## Environment

Windows: `_dupenv_s(&variable_value, &value_length, "VARIABLE")`

Linux: `char* variable_value = getenv("VARIABLE")`

## Files

```cpp
#include <fstream>
#include <iostream>
#include <string>

int main() {
    // Write to file
    std::ofstream out("example.txt");
    if (!out.is_open())
    {
        throw std::runtime_error(std::string() + "Could not open file");
    }

    std::string content = "...";
    out.write(content.c_str(), content.size());

    out << "Hello, file!" << std::endl;
    out.close();

    // Read from file
    std::ifstream in("example.txt");
    if (!in.is_open())
    {
        throw std::runtime_error(std::string() + "Could not open file");
    }

    std::string line;
    while (std::getline(in, line))
        std::cout << line << std::endl;
    in.close();

    int size = 1024;
    char result[size];
    in.read(result, size);

    // Open in binary mode.
    std::ofstream file;
    file.open(file_path, std::ofstream::out | (binary ? std::ofstream::binary : 0));
}
```

## `std::map` — Key–Value Operations

```cpp
#include <iostream>
#include <map>
#include <string>

int main() {
    // === 1. Constructors ===
    std::map<std::string, int> ages;  // empty map

    // Initializer list constructor
    std::map<std::string, int> scores = {
        {"Alice", 90},
        {"Bob", 85},
        {"Charlie", 95}
    };

    // Copy constructor
    std::map<std::string, int> copyScores(scores);

    // === 2. Insert and Assign ===
    // Cpp17 insert_or_assign - always updates value (even if exists)
    ages.insert_or_assign("Tom", 31);
    ages.insert_or_assign("Spike", 40);

    // === 3. Access ===
    std::cout << "\nAccess by key:" << std::endl;
    // at() throws exception if key is not found - better than []
    std::cout << "Tom: " << ages.at("Tom") << std::endl;

    // === 4. Iteration ===
    std::cout << "\nAll entries:" << std::endl;
    for (const auto& items : ages)
        std::cout << items.first << " -> " << items.second << std::endl;

    // === 5. Find and Erase ===
    auto it = ages.find("Spike");
    if (it != ages.end()) {
        std::cout << "\nErasing: " << it->first << std::endl;
        ages.erase(it);
    }

    return 0;
}
```

## `std::vector` — Dynamic Array Operations

```cpp
#include <iostream>
#include <vector>
#include <algorithm> // for std::find

int main() {
    // === 1. Constructors ===
    std::vector<int> v1;                   // empty
    std::vector<int> v2(5, 42);            // {42,42,42,42,42}
    std::vector<int> v3 = { 1, 2, 3, 4, 5 }; // initializer list
    std::vector<int> v4(v3.begin(), v3.end()); // copy from range

    // === 2. push_back / emplace_back ===
    v1.push_back(10);
    v1.push_back(20);
    v1.emplace_back(30);  // constructs in-place

    std::cout << "v1 contents: ";
    for (int x : v1) std::cout << x << " ";
    std::cout << std::endl;

    // === 3. Access ===
    // at() is better than [] - throws std::out_of_range on error
    std::cout << "Second element (at()): " << v3.at(1) << std::endl;

    // === 4. Iteration ===
    std::cout << "v3 elements: ";
    for (auto it = v3.begin(); it != v3.end(); ++it)
        std::cout << *it << " ";
    std::cout << std::endl;

    // === 5. find() ===
    auto it = std::find(v3.begin(), v3.end(), 3);
    if (it != v3.end())
        std::cout << "Found 3 at index " << (it - v3.begin()) << std::endl;

    // === 6. Append another vector ===
    std::vector<int> chunk = { 6, 7, 8 };
    v3.insert(v3.end(), chunk.begin(), chunk.end());
    std::cout << "After append: ";
    for (int x : v3) std::cout << x << " ";
    std::cout << std::endl;

    // === 7. Erase elements ===
    v3.erase(v3.begin(), v3.begin() + 2);  // erase first two
    std::cout << "After erase first 2: ";
    for (int x : v3) std::cout << x << " ";
    std::cout << std::endl;

    // === 8. Other useful methods ===
    std::cout << "Size: " << v3.size() << std::endl;
    std::cout << "Front: " << v3.front() << ", Back: " << v3.back() << std::endl;

    return 0;
}
```

## Diamond Inhertiance Problem & Virtual Inheriance

- Virtual functions (`virtual void f()`): solve _which override to call_ (dynamic dispatch). They do not prevent having two separate base subobjects in a diamond.
- Virtual inheritance (`struct B : virtual A {}`): makes the most-derived class hold one shared `A` subobject, removing duplication/ambiguity of state.

#### Without virtual inheritance — duplicate `A`

```cpp
struct A { int x = 0; };
struct B1 : A {};
struct B2 : A {};
struct D : B1, B2 {}; // diamond

D d;
// d.A::x is ambiguous; there are two A subobjects: via B1 and via B2
```

#### With virtual inheritance — single `A`

```cpp
struct A { int x = 0; virtual ~A() = default; };
struct B1 : virtual A {};
struct B2 : virtual A {};
struct D : B1, B2 {
    D() { x = 42; }  // OK: there's only one A subobject
};
```

### Notes

- The most-derived class (`D`) is responsible for constructing the virtual base (`A`) in its constructor initializer list:

  ```cpp
  struct D : B1, B2 {
      D() : A{} {}   // initialize the virtual base
  };
  ```

- Access may still need qualification if multiple intermediate bases define members with the same name.
- Virtual functions work orthogonally: if `A::f` is virtual and overridden in `B1/B2/D`, dynamic dispatch chooses the most-derived override, but you still need virtual inheritance to avoid duplicate `A` state.

---

## Networking

`htons()` - converts little endian to big endian

### Server

```cpp
#include <boost/asio.hpp>
#include <iostream>
#include <string>

using boost::asio::ip::tcp;

int main() {
    try {
        unsigned short port = 12345;
        boost::asio::io_context io_context;
        tcp::acceptor acceptor(io_context, tcp::endpoint(tcp::v4(), port));

        std::cout << "Server listening on port 12345...\n";

        for (;;) {
            tcp::socket socket(io_context);
            acceptor.accept(socket);

            std::cout << "Client connected!\n";

            // To prevent block:
            // std::thread(handle_function, socket).detach();

            // Read message from client
            char data[max_length];
            boost::asio::read(s,boost::asio::buffer(data, max_length));
            std::cout << "Received from client: " << data;

            // Reply to client
            std::string response = std::string() + "Server received: " + data;
            boost::asio::write(socket, boost::asio::buffer(response.c_str(), response.size()));
        }
    } catch (std::exception& e) {
        std::cerr << "Server error: " << e.what() << std::endl;
    }
}
```

---

### Client

```cpp
#include <boost/asio.hpp>
#include <iostream>
#include <string>

using boost::asio::ip::tcp;

int main() {
    try {
        char* address = "127.0.0.1";
        char* port = "1234";
        boost::asio::io_context io_context;
        tcp::socket socket(io_context);
        tcp::resolver resolver(io_context);
        boost::asio::connect(socket, resolver.resolve(address, port));
        std::cout << "Connected to server.\n";

        // Send message
        std::string msg = "Hello from client!\n";
        boost::asio::write(socket, boost::asio::buffer(msg.c_str(), msg.size()));

        // Read response
        char data[max_length];
        boost::asio::read(s,boost::asio::buffer(data, max_length));
        std::cout << "Response from server: " << data << std::endl;

    } catch (std::exception& e) {
        std::cerr << "Client error: " << e.what() << std::endl;
    }
}
```

### Cryptopp

Download and extract -https://www.cryptopp.com/ -> Downloads

Build and add lib to link libraries, add directory as include directory.

### Boost

Download and extract - https://www.boost.org/releases/latest/

Note: To use `asio` you don't need to build it.

---

# Python

## Docs

https://docs.python.org/3/tutorial

## Examples

```python
import string
import random

# Base Class
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):
        # Defines what str(obj) returns
        return f"Person(name={self.name}, age={self.age}, traits={self.traits})"

    def __getattr__(self, item):
        # Called *only if* attribute not found normally
        print(f"[__getattr__] '{item}' not found, returning default None")
        return None

    def __getattribute__(self, item):
        # Called for every attribute access
        print(f"[__getattribute__] Accessing '{item}'")
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        # Called for every attribute assignment
        print(f"[__setattr__] Setting '{key}' = {value}")
        super().__setattr__(key, value)

    def __lt__(self, other):
        # Called on < usage
        return self.age < other.age

    # Adding `__` performs changes name but does not really hide.
    def __pseudo_hidden():
      pass

# Derived Class
class Student(Person):
    def __init__(self, name , age, grades):
        super().__init__(name, age)
        self.grades = grades

    def add_grade(self, grade):
        self.grades.append(grade)

    def get_grades(self):
        return self.grades


# Function example
# - Required parameters
# - Optional parameters
# - kwargs - generic arguments in form a,b,c
# - kwargs - generic arguments in form k1=v1,k2=v2,
def func(name, age=0, *args, kwargs):
    print({"name": name, "age": age, "args": args, "kwargs": kwargs})

# Decorator - a function that gets a function and returns a wrapper function.
def timer_decorator(func):
    def wrapper(*args, kwargs):
        start_time = time.time()
        result = func(*args, kwargs)
        end_time = time.time()
        print(f"Function '{func.__name__}' executed in {end_time - start_time:.4f} seconds.")
        return result
    return wrapper

def main():
    # Dictionaries
    details = {"major": "Computer Science", "year": 2}
    year = details["year"]
    for key, value in details.items():
        print(f"{key}={value}")

    # Lists
    lst = [1,2,4]
    lst.insert(2, 3)
    lst.append(5)
    print(sum(lst))

    # Strings
    # Constants
    chars = string.ascii_letters + string.digits
    # `str.split()` - splits by space or newline

    # Random choice
    print(random.choice(chars))

    # Functions
    func("bob")
    func("bob", 1)
    func(name="bob", age=1)
    func("bob", 1, 2, 3, d=4, e=5)

    # Objects
    s = Student("Alice", 20, [70, 80])
    s.add_grade(95)
    print(s.get_grades())

    print("\n--- Access attributes (triggering __getattribute__) ---")
    print(s.name)
    print(s.age)

    print("\n--- Access a missing attribute (trigger __getattr__) ---")
    print(s.non_existent_field)

    print("\n--- Print object (trigger __str__) ---")
    print(s)

    print("===== metaprogramming =====")
    print(f"Object attributes: {dir(s)}")
    print(f"Object class: {s.__class__}")
    print(f"Object base classes: {s.__class.__.__bases__}")

    print("Monkey patching:")
    import math
    original = math.sin
    math.sin = lambda x: 41
    print(math.sqrt(30)) # 1

    print("setattr, getattr")
    class C: pass
    c = C()
    setattr(c, 'num', 1)
    # getatter() will call __getattribute__ on normal access and __getattr__ on special access.
    print(getattr(c, 'num')) # 1

    print("inspect")
    import inspect
    def func(num): return num
    print(inspect.signature(func)) # (num)
    print(func.__name__) # 'func'

    # Decorating all the methods of an object:
    # @classmethod
    # def class_method(cls):
    #     for attribute, item in cls.__dict__.items():
    #         if callable(item):
    #             setattr(cls,attr,decorator(item))
    with open(filename, permissions) as file:
        content = file.read(1024)
        file.write(content)

    # - Default permission is read - "r"
    # - Write (deletes current content)  - "w"
    # - Append - "a"
    # - Binary mode - "b"
    # - Read/write with existing file - "r+"
    # - Read/write with new file (deletes current content) - "w+"

if __name__ == "__main__":
    main()
```

- `range(50,60)` returns type `range`
- `[[1, 2, 3],[4, 5, 6]].copy()` - shallow copy
- Copy - default is shallow copy

## Networking

### Error Handling

```python
try:
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ...
except socket.error as e:
    ...
except socket.timeout:
    ...
```

### Client

```python
import socket

HOST = "127.0.0.1"
PORT = 1234

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))

    # sendall is better than send - actually sends all information
    client_socket.sendall("Hello World".encode('utf-8'))
    data = client_socket.recv(1024)
    print(data)
```

- IPv6 - address is 128 bit, use `AF_INTET6` sockets.

### Server - Using threads

```python
import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break  # client disconnected
            message = data.decode('utf-8')
            print(f"[{addr}] {message}")
            conn.sendall(f"Echo: {message}".encode('utf-8'))
    print(f"[DISCONNECT] {addr} disconnected.")


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[LISTENING] Server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[SERVER SHUTDOWN]")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
```

### Server - Using select

```python
import selectors
import socket
selector = selectors.DefaultSelector()

def accept_client(socket_, mask):
    client_socket, client_address = socket_.accept()
    print(f"New connection from {client_address}")
    client_socket.setblocking(False)
    selector.register(client_socket, selectors.EVENT_READ, read_client)

def read_client(client_socket, mask):
    data = client_socket.recv(1024)
    if data:
        print(f"Echo: {data}")
        client_socket.sendall(data)
    else:
        print(f"Closed connection: {client_socket}")
        selector.unregister(client_socket)
        client_socket.close()

server_socket = socket.socket()
server_socket.bind(('localhost', 1234))
server_socket.listen(100)
server_socket.setblocking(False)
selector.register(server_socket, selectors.EVENT_READ, accept_client)

while True:
    events = selector.select()
    for key, mask in events:
        callback = key.data
        callback(key.fileobj, mask)

```

- mask - bitmask that contains information, such as error / ready for reading / ready for writing

---

## Struct

```python
import struct

# B - uint8_t
# H - uint16_t
# I - uint32_t
# < - little endian
packed = struct.pack('<IB', 1, 2)
print(packed)

num1, num2 = struct.unpack('<IB', packed)
print(num1, num2)
```

## Descriptors

Python descriptors are objects that customize attribute access on a class.
If an attribute stored on a class defines any of `__get__`, `__set__`, or `__delete__`, Python routes this attribute access through those methods.

Call logic:

```py
value = descr.__get__(obj, type(obj))         # on instance access
value = descr.__get__(None, Cls)              # on class access
descr.__set__(obj, value)                     # on assignment: obj.attr = value
descr.__delete__(obj)                         # on del obj.attr
```

Types:

- **Data descriptor**: defines `__set__` and/or `__delete__`. Takes precedence over instance attributes.
- **Non-data descriptor**: defines only `__get__`. Instance attributes override it.

Example:

```py
class UpperCase:
    def __get__(self, obj, owner):
        return obj._name.upper()

class Person:
    name = UpperCase()
    def __init__(self, name): self._name = name

p = Person("Ada")
print(p.name)  # "ADA"
```

---

# Networking

## DNS over UDP or TCP

- Default: DNS uses UDP (single datagram) because it’s fast and lightweight.

- When TCP is used:

  - If the response doesn’t fit in UDP (even with EDNS0) or the server sets TC=1 (Truncated), the client retries over TCP.
  - Zone transfers (AXFR/IXFR) always use TCP.

- Security angles:

  - UDP is easier to spoof and enables amplification attacks.
  - TCP is less spoof-friendly (3-way handshake) but heavier and stateful.

---

# SQL

SQL, or Structured Query Language, is a domain-specific programming language designed for managing and manipulating relational databases. It is the standard language used to interact with and extract information from these databases.

SQL is primarily used with RDBMS (Relational Database Management Systems), which store data in a structured, tabular format with rows and columns. Examples include MySQL, Oracle, PostgreSQL, and Microsoft SQL Server.

## Useful Commands

```SQL
CREATE TABLE Table(column1 datatype, column2 datatype,…);
CREATE TABLE Users(UserID int NOT NULL PRIMARY KEY, UserName varchar(255), Age int);

INSERT INTO Table VALUES (value1, value2, ...);
INSERT INTO Users VALUES (123, "Dan", 12);

UPDATE Table SET column1 = value1, column2 = value2, … WHERE condition;
UPDATE Users SET Age = 12 WHERE UserID = 123;

SELECT column1, column2, … FROM Table WHERE condition;
SELECT * FROM Table WHERE condition;
SELECT UserID, UserName FROM Users WHERE age >= 12;

DELETE FROM Table WHERE condition;
DELETE FROM Users WHERE UserID = 123;
```

## SQL in Python

```python
import sqlite3

# Connect
conn = sqlite3.connect('databasename.db')

# Use this to return TEXT as bytes and not str (if storing non-readable strings)
conn.text_factory = bytes

# Execute without data
conn.executescript(query)

# Execute with data
cur = conn.cursor()
cur.execute(query)
rows = cur.fetchall()

row = cur.fetchone()
value1, value2, value3 = row

# Parameterized queries
cur.execute("QUERY ... VALUES (?, ?, ?);", (value1, value2, value3))

# Save changes
conn.commit()

# Close
conn.close()
```

## SQL in Cpp

```cpp
#include "sqlite3.h"

...

sqlite3* db = nullptr;
char *query = nullptr;
char* error = nullptr;
int result = 0;


result = sqlite3_open("database.db", &db);
if (result != SQLITE_OK) { /* error */ }

query = "QUERY;";
result = sqlite3_exec(db, query, nullptr, nullptr, &error);
if (result != SQLITE_OK) { /* error */ }

sqlite3_close(db);
```

---

# Cloud Computing

- Useful design - server can have many resources (compute, storage, etc.) and clients only need to login. They can be used from anywhere.
- Sometimes we will want the server to run code - then we need to find ways to limit it and prevent attacks.
- Commands can be split to local and system commands, and make all system commands be handled by an external process. Then the server can choose to deny some commands. `PyPy` uses this.
- Remote method invocation - instead of letting user run arbitrary code, we will give list of functions that can be executed remotely.
  - Then we only need to make sure they are secure.
  - Efficient implementation - make functions genericly serializable and send them on the network, Create a metaclass that will wrap all methods and send them remotely when called.
- See also: `Remote Code Exeuction (RCE)` below.

# Security

## Definitions

- Bug - A _bug_ is an unintended flaw or error in software that causes it to behave incorrectly.
- Vulnerability - A _vulnerability_ is a weakness in software or a system that can be exploited to cause unintended behavior — often leading to unauthorized access, data leaks, or service disruption.
- Exploiting - _Exploiting_ (or _an exploit_) is the act or method of taking advantage of a vulnerability to achieve a malicious goal — such as executing arbitrary code or escalating privileges.
- Mitigation - _Mitigation_ refers to techniques or controls that reduce the risk or impact of a vulnerability or attack.
- Security - _Security_ in a system context means the protection of information and operations against unauthorized access, use, modification, or destruction.
- Reliability - _Reliability_ means the system consistently performs its intended functions under expected conditions.
- Privacy - _Privacy_ is about protecting personal or sensitive information from being disclosed without consent.
- Run-Time Environment - A _runtime environment_ is the context in which a program executes — including the system libraries, memory layout, permissions, and interpreter or virtual machine.
- Sandbox - A _sandbox_ is an isolated environment for running code safely, so it can’t affect the rest of the system.
- Threat tree - summary of known attack paths (similar to user stories) and mitigations for them.
- Component threats - derived from individual components.
  System threats - derived from the host environment or the design / connection of components to one another (DoS, Side channel, )
- System mitigations - general security best practices and ideas (anti-viruses, sandbox...)
  Specific mitigations - protect against specific scenarios and attacks.
- CISO - Chief Information Security Officer - responsible for entire security of a company.

## Principals

- Minimum principal - give every module minimum permissions.
- Validation principal - validate length, type, content.
- Modularity - if one module is compromized, the rest are secure.
- Continuous updates - to close bugs and vulnerabilities.
- Layering - using multiple strategies and mitigations reduces the probability of successful exploitation.

## Attacks

Attack types (arbitrary partition):

- Brute force
- Privilege Escalation
- Buffer overflow
- Man in the middle (MITM)
- Code Injection
- Denial of service (DOS)

## Brute-Force Attacks

Systematic guessing of secrets (passwords, keys, tokens). Variants differ by source of guesses and where they’re applied.

### Examples

- Online brute force (against a live service):

  - Password spraying: Try one common password across many accounts to avoid lockouts.
  - Credential stuffing: Use leaked email:password combos against other sites.

- Offline cracking (against stolen hashes or encrypted blobs) - Dictionary or rule-based to break hashes (NTLM, SHA-1, etc.).

- API token / short link guessing if identifiers have low entropy (small amount of possible options).

Why attackers succeed: Weak passwords, password reuse, poor rate limiting, informative error messages (account enumeration), fast/unsalted hashes, no MFA.

### Mitigations

- Strong authentication:

  - Multi Factor Authentication, ideally phishing-resistant.
  - If passwords remain: enforce length + complexity that resists guessing (passphrases), no reuse, check new passwords against breached lists.

- Rate controls:

  - Progressive delays, per-IP/ASN/app-token rate limiting, SYN/connection limits at edge.
  - Lockout / step-up after few failures (but protect from trivial DoS by using cooldowns, CAPTCHA, or risk-based auth).

- Detection & response:

  - Credential-stuffing signatures (odd user-agents, high failure rates, replay patterns).
  - Impossible travel, device fingerprint, IP reputation, velocity rules, alerting.

- Good password storage (for offline risk):

  - Use Argon2id (preferred) or bcrypt/scrypt with strong parameters; unique salt per hash; add pepper at the app tier if suitable.

- Protocol & UX hardening:

  - Generic failure messages (avoid account enumeration).
  - Enforce HTTPS/HSTS; protect login endpoints with WAF/bot defenses; throttle OTP attempts; bind OTP to device/time window.
  - Don't let the system give feedback on correct/incorrect input. 
  - Create many possible combinations or delay between attempts.

## Privilege Escalation
Users and groups can be given very little permissions to resources by default. An attacker's purpose is to gain more - privilege escalation.

Is bug: No

### Examples 

- Hacking into database to get users credentials.
- Vertical - gain more permissions (i.e admin).
  Horizontal - gain permissions to other users with same permissions.

### Mitigations

- Least Privilege: Grant users and applications only the minimum permissions necessary.
- Strong Authentication: Enforce strong password policies and multi-factor authentication.

## Buffer Overflow

Writing past array bounds.

Is bug: Yes

### Examples

- `scanf()` to a local buffer variable without boundary, and then write a different return address on the stack.
- When entering a username, write a long answer so that the password field will be overriden.
- Writing into the vtable of an object so the actual called function will be different.

### Mitigations

- Use `strncpy`, `memcpy_s` in C/Cpp or safe containers like `std::string`.
- Enable stack canaries - puts a constant between local variables and return address - recognizes if it was overriden.
- Enable ASLR - puts functions and objects in different locations in memory each run.

## Man-in-the-Middle (MITM)

An attacker secretly interposes between two parties and reads/changes traffic while making each side believe they’re talking directly to the other.

### Examples

- Rogue Wi-Fi / Evil Twin: Attacker creates a hotspot named like a real one; victims connect and all traffic is proxied/sniffed.
- ARP spoofing (LAN): Poisoning ARP tables so victims send traffic to the attacker’s MAC; attacker forwards to the real gateway.
- DNS spoofing/hijack: Tamper with DNS answers so victims go to attacker-controlled servers.

### Mitigations

- End-to-end encryption: Always use TLS (HTTPS, SMTPS, IMAPS). Prefer HSTS, TLS 1.2+, strong ciphers.
- Certificate validation: distrust unknown CAs, watch for cert warnings.
- Secure DNS: DNS over TLS/HTTPS to a trusted resolver; DNSSEC validation (validates DNS data itself).
- Wi-Fi: WPA2-Enterprise/WPA3, disable open SSIDs, use per-user creds or EAP-TLS.

## Side-Channel Attacks

Leaking info via third-party modules and systems.

Is bug: No

### Examples

- Use clock to control random number generation.
- Use power consumption to understand how many characters of a password are correct.
- Attack host system or network and gain control of private key.

### Mitigations

- Use constant-time cryptographic operations (i.e run action on all bytes, no matter how many are correct).
- Add random wait time for validation processes. 
- Isolate sensitive code (TPM, hardware modules).

## Denial of Service (DoS)

Flooding server with requests.

Is bug: No, but some implemenations are more vulnerable than others.

### Mitigations

- Rate limiting.
- Circuit breakers - if flooded with requests, do not pass some of them on so the system will not overflow.
- Create scalable code - does not require more resources if getting a lot of requests (e.g. `select`, reactor pattern).

## Remote Code Execution (RCE)

Unsafely executing user-supplied code.

Is bug: Yes

### Examples

- Dynamic code execution
  - `compile()` used to compile code, can be executed with `exec(code, globals(), locals())`.
  - `eval(code)` - runs code directly
  - They run arbitrary code, dangerous because of potential malicious code injection (i.e using `command1 ; command2`).
  - Example: `eval("__import__('os').system('rm -rf /')")`
- `input()` - in python 2 it gets user input and is interpreted as code.
  If a variable `password = 123` exists and the user inputs `password` then the return value will be `123`. `raw_input()` should be used in python 2.
- Pickle module - serializes code, dangerous because an attacker can run code on target (deserilizer) machine
- Dynamic import: `import importlib; module = importlib.import_module('socket')`

### Mitigations

- Never use `eval` or `exec` on untrusted data.
- Disable imports: `exec(code, {'__builtins__': None}, {})`.
  - Trying to bypass import limit - `(2,3).__class__.__base__.__subclasses__()`
- Use sandboxing or virtual machines.
- Giving only specific lists of functions to run (remote method invocation).

## SQL Injection

Run SQL queries using by providing crafted user input.

Is bug: Yes

### Mitigations

- Use parameterized queries
  ```python
  cur.execute("SELECT * FROM Table WHERE Name = ? AND City = ?",[name,city])
  ```
- Validate input types.
- Escape strings safely.

## Heap Spraying

An attacker manipulates an application to allocate many objects containing malicious code in the heap, increasing the success rate of an exploit that jumps to a location within the heap

Is bug: No

### Mitigations

- Enable ASLR and DEP.
- Use safe allocators (guard pages, canaries, randomization - similar to stack protections).
- Randomize heap structures.

## Return Oriented Programming (ROP)

Reusing existing code (gadgets) for malicious execution.

Is bug: No

### Examples

### Mitigations

- Enable ASLR and Control Flow Integrity.
- Use non-executable stack/heap.

## IP or TCP layer IDS Evasion

Is bug: No

An attacker splits packets so that middleboxes (IDS/firewalls) and the end host reassemble differently. If the IDS “sees” one byte stream but the OS reconstructs a _different_ one, malicious content can slip past detection.

### Examples

- Send overlapping IPv4 fragments or overlapping TCP segments.
- Some reassembly policies choose “first wins,” others “last wins,” or follow OS-specific quirks.
- The IDS might treat the stream as harmless; the endpoint’s OS reconstructs harmful input (e.g., different HTTP request).
- Classic example: _Teardrop_ and other malformed fragments that lead to incorrect length calculations → crash/overflow on the target stack.

### Mitigations

- Make the IDS/firewall emulate the target OS reassembly behavior (OS fingerprinting + matching policy).
- Normalize traffic: drop malformed/overlapping fragments, enforce sane TTL/DF, clamp segment sizes.

## UDP Amplification & Spoofing

UDP is stateless, so it’s easy to spoof source IPs. If a service replies with much larger responses than the query, it becomes a reflector/amplifier.

Is bug: No

### Exapmles

- DNS amplification: attacker sends small spoofed queries (pretending to be the victim) to open resolvers; resolvers send large responses to the victim.

### Mitigations

- Stop spoofed traffic at ISPs and enterprise edges.
- Rate limiting, per-IP/AS limits.
- Application hardening: minimal responses, authentication for UDP services, disable legacy amplifying commands.

## TCP Spoofing / Injection

TCP connections start with sequence numbers (ISN). If ISNs are predictable, an attacker can spoof a 3-way handshake or inject data into an existing flow.

Is bug: No

### Mitigations

- Use strongly random ISNs (RFC-style cryptographic mixing of 4-tuple + secret).

## TCP SYN Flood

Send many SYNs (often spoofed). The server allocates half-open connection state and waits for the final ACK.The table fills so the legit clients can’t connect.

Is bug: No

### Mitigations

- SYN cookies: don’t allocate per-connection state on SYN. Instead, encode state into the SYN-ACK’s sequence number; only allocate if a valid ACK returns.

  - Pros: very effective under flood.
  - Caveats: limits some TCP options during attack, but modern stacks handle this gracefully.

- Backlog tuning & timeouts: increase `listen()` backlog, reduce SYN-ACK retries/timeouts, use larger connection queues.
- Distribute load: SYN proxy on Load Balancer/firewall, anti-DDoS services.
- Rate-limits / filters: throttle obvious offenders at ACLs/iptables.

## DNS Cache Poisoning

Make a recursive resolver cache a forged answer so clients get redirected to an attacker’s IP.

Requirements for the attacker: Their fake reply must match the outstanding query (TXID, source port, question name/type, etc.) and arrive first.

### Mitigations

- DNSSEC – cryptographic signatures on DNS records; validates authenticity (the fundamental fix).
- More entropy – randomize TXID and source port; optionally use 0x20 case randomization on QNAME.
- Operational controls – rate limiting (RRL), monitoring for anomalies, don’t run open resolvers (limit use only for your DNS server).

## FTP Bounce

In active FTP, the client sends `PORT <ip,port>` telling the server where to open the data connection. An attacker can abuse this to make the FTP server connect to a third party (internal host/port), effectively “bouncing” scans or data through the server.

### Mitigations

- Prefer PASV (passive) mode so the client initiates the data connection.
- On servers, restrict/validate `PORT`: only allow the client’s IP, block reserved/internal targets, or disable PORT entirely.
- Egress filtering on the FTP server; replace legacy FTP with SFTP/FTPS where feasible.

## SMTP Open Relay

An open relay lets anyone send mail to anywhere via your server, which allows users to send spam and will make hurt your IP or domain reputation damage, or even make it blacklisted.

### Mitigations

- Require SMTP AUTH and restrict relay to authenticated users or trusted networks.
- Deploy SPF, DKIM, and DMARC to authenticate senders and publish handling policy.
- Use rate limiting, greylisting, and sensible acceptance policies.

## XSS — Cross-Site Scripting

An attacker gets their JavaScript to run in a victim’s browser in the context of your site. That script can read data the page can read (e.g., session-bearing cookies if not `HttpOnly`), make API calls as the user, alter the DOM, etc.

### Examples

- Stored (persistent): Malicious input is saved on the server (e.g., a comment) and served to every viewer.
- Reflected: The payload comes from the request (URL/form) and is reflected in the response.
- DOM-based: The page’s own JS takes untrusted data (e.g., `location.hash`) and injects it into the DOM unsafely.

### Mitigations

- Output encoding/escaping by context (HTML text vs attribute vs JS vs URL). Prefer template engines with auto-escaping.
- CSP (Content-Security-Policy) to block inline scripts and restrict sources.
- Input validation (whitelists) to reduce dangerous inputs, but still escape on output.
- HttpOnly & Secure cookies, avoid reflecting untrusted input into scripts, and prefer same-site navigation patterns.

## CSRF — Cross-Site Request Forgery

An attacker tricks a logged-in user’s browser into sending a legitimate-looking request to your site (e.g. “transfer money”) without the user’s intent. The browser automatically includes cookies (session), so the server thinks it’s the user.

### Examples

- An attacker page can auto-submit a hidden form to that URL. The victim’s browser attaches the session cookie, and the server applies the change.

### Mitigations

- CSRF tokens (synchronizer pattern): unique, unpredictable token per session/form, verified server-side.
- SameSite cookies (`Lax`/`Strict`) to limit cross-site cookie sending.
- Check `Origin`/`Referer` as an additional signal (not sole control).

## Cpp-Specific Attacks

- Integer overflow (MAX_INT -> 0) - can be used to make program allocate create small buffers, so the attacker will perform buffer overflow.
- Use-After-Free (UAF) - attacker saves a pointer that was once used, makes system allocate another struct in the same area, and then gain access system components. To prevent - NULLify after free.

---

# Mitigations

## ASLR

Address Space Layout Randomization (ASLR) randomizes memory layout (stack, heap, libraries, executable base) so that attackers cannot predict addresses needed for many memory corruption exploits.

### Implementation

- How it works: OS kernel chooses randomized offsets when mapping libraries, heap, stack; combined with other mitigations (NX, DEP) it greatly raises the difficulty of code reuse attacks.
- How to disable it in linux (testing only; disabling in production is unsafe): `echo 0 | sudo tee /proc/sys/kernel/randomize_va_space`) (`echo 1` to enable).

## Analysis (static and dynamic)

Static analysis examines program code or binaries without executing them (linting, SAT/SMT-based checks, pattern matching).

Dynamic analysis inspects program behavior at runtime (fuzzing, instrumentation, debuggers, runtime monitoring). Both are analysis methods used to find defects and vulnerabilities.

### Implementation

- Static analysis
  - Tools: linters, type checkers, static analyzers, binary scanners.
  - Strengths: early detection, broad code coverage, no need to run untrusted code.
  - Weaknesses: false positives, limited visibility into runtime behavior and environment-specific bugs.
- Dynamic analysis
  - Tools: fuzzers, sanitizers (detect memory errors), debuggers, runtime profilers.
  - Example: using Valgrind to detect memory leaks and buffer overflows.
  - Strengths: finds bugs that manifest only at runtime (race conditions, memory corruption).
  - Weaknesses: requires workloads / inputs to exercise code paths; may miss rare paths.

### Virus Signature-Based Detection

Identifies threats by comparing files or data against a database of known malicious patterns, or "signatures". These signatures are unique identifiers, such as specific code sequences, generated from previously identified malware. When a file is scanned, the antivirus software checks for a match with a signature in its database; a successful match indicates a potential threat.

Helps to generally find viruses in a system, and prevent their execution.

## Sandbox

A sandbox is an isolated execution environment that restricts a program’s access to system resources (files, network, devices, other processes) to limit potential damage from buggy or malicious code.

### Implementation

- Techniques:
  - Process isolation: run code with constrained privileges (chroot, seccomp, capability drops, Windows Job Objects).
  - Split-process / internal-external architecture: separate sensitive operations into a small, privileged “core” process and run untrusted or high-risk logic in a less-privileged external process. Example: some VMs and language runtimes (and the user-mentioned PyPy approach) use out-of-process sandboxes for JIT'd code or foreign code execution.
  - Virtualization: full VMs isolate at the hardware/virtual hardware level — strong isolation but heavier weight.
  - Containers: lighter-weight isolation using kernel namespaces and cgroups; good for process isolation but share a kernel with the host (so kernel vulnerabilities matter).
  - Language runtime sandboxes: restricted interpreters that block specific syscalls or APIs.
- Use-cases:
  - Running browser tabs, plugin code, PDF rendering, online code judge systems, malware analysis labs.
- Tradeoffs:
  - Security vs. convenience: stricter sandboxes reduce functionality. Containers are easier to deploy; VMs provide stronger isolation.

## Control Flow Integrity (CFI)

Also called: control-flow enforcement technology (CET)

Control Flow Integrity enforces that a program’s runtime control-flow (which functions can call which other functions, and which return addresses are valid) follows a precomputed legitimate graph so that memory corruption can’t divert execution to arbitrary locations.

### Implementation

- Shadow stack:
  - A common CFI technique to protect returns: maintain a separate, protected stack of return addresses (the _shadow stack_) that cannot be corrupted by normal buffer-overflow writes. On function return, the runtime compares the actual return address with shadow stack entry; mismatch indicates an attack.
  - Implementation requires compiler support and runtime kernel features to protect the shadow stack memory (e.g., make it non-writable to normal code).
- Deployment:
  - Many modern compilers (clang, gcc) provide CFI options; OSes may also implement kernel-level support (e.g., Intel CET for shadow stack support).

## Code Obfuscation

Code obfuscation is transforming source or binary code to make it harder to analyze and understand while preserving functionality; primarily used to raise the difficulty/cost of reverse engineering.

### Implementation

- Techniques:
  - Identifier renaming, control-flow flattening, opaque predicates, junk instructions, string encryption, virtualization/translation (translate bytecode into a custom VM).
  - Binary-level obfuscation: packers, anti-debugging tricks, API-hiding.
- Use-cases:
  - Protecting IP, licensing checks, deterring casual reverse engineering.
- Drawbacks:
  - Not a replacement for strong security; determined attackers can deobfuscate. Obfuscation increases maintenance complexity and can introduce bugs or performance penalties.

## Vulnerability Indexes

Vulnerability indexes are structured systems used to categorize, prioritize, and compare vulnerabilities across software and time. They help in risk triage and remediation planning.

### Implementation

- Why they exist: to provide a common language for severity, exploitability, and impact so organizations can prioritize fixes and measure progress.
- Examples and components:
  - CVSS (Common Vulnerability Scoring System): numeric score (0–10) that encodes attack vector, complexity, privileges required, user interaction, impact on confidentiality/integrity/availability, and temporal/environmental modifiers.
  - CWE (Common Weakness Enumeration): taxonomy of types of software weaknesses (e.g., CWE-79 Cross-site Scripting, CWE-119 Buffer Overflow). Helps classify root cause and improve secure practices.

## Non-Executable Stack and Heap / Data Execution Prevention (DEP)

A non-executable (NX) stack/heap marks memory regions used for data (like stack or heap) as non-executable, preventing code injected into those regions from being executed directly.

### Implementation

- Mechanism:
  - The hardware-supported NX bit (or XD on Intel) marks memory pages as non-executable. The OS enforces this mapping via page table permissions.
- Effect:
  - Stops simple code-injection attacks where shellcode is placed on the stack/heap and then jumped to.
  - Attackers adapt with return-oriented programming (ROP) and other code-reuse techniques, so NX is necessary but not sufficient.

## SafeSEH

SafeSEH (Safe Structured Exception Handling) is a Windows-specific mitigation that restricts exception handler addresses to a validated list in the binary’s load-time table, preventing an attacker from using arbitrary exception handlers to gain control.

### Implementation

- Mechanism:
  - Windows PE executables can include a table of valid exception handlers. When an exception occurs, the OS checks that any handler used is in the table; if not, the handler is rejected.
- Notes:
  - SafeSEH historically applied to 32-bit Windows PE files and required cooperation at link-time. Newer mitigations and 64-bit Windows have different exception handling models and protections.
- Tradeoffs:
  - Helps block certain exploit primitives but must be used with other mitigations (ASLR, DEP, CFI).

## Function Pointer Obfuscation

Function pointer obfuscation hides or mangles function pointers at runtime so that an attacker who obtains memory cannot easily determine or overwrite the true target functions.

### Implementation

- Techniques:
  - XOR/encrypt function pointers when stored in memory and decrypt them on use.
  - Add per-process/per-instance randomization keys (pointer encoding).
  - Use indirection tables with integrity checks (hash-based validation).
- Tradeoffs:
  - Raises bar for attackers but must be done correctly (key management, protection of decoding routine).
  - Can be combined with CFI for stronger guarantees.

## Trusted Platform Module (TPM)

A Trusted Platform Module (TPM) is a hardware security module (a discrete chip or firmware module) that provides secure cryptographic functions and protected storage for keys, measurements, and attestation — designed to resist software-based attacks.

### Implementation

- Capabilities / APIs:
  - Random number generation: hardware entropy sources for cryptographic randomness.
  - Key generation & storage: create asymmetric keys inside the TPM and keep private keys non-exportable.
  - Digital signatures & encryption: TPM can sign or decrypt using keys that never leave the module.
  - Sealing: bind secrets to platform state (PCRs) so keys or secrets can only be unsealed when the system is in a known good state.
- Protection against side channels:
  - The TPM’s isolation reduces the risk that private keys are trivially read by software; however, TPMs can still be subject to sophisticated physical side-channel analysis (power, EM) if an attacker has physical access. TPMs reduce the attack surface for software-based side channels by not exporting sensitive key material.
- Practical uses:
  - Disk encryption key storage (e.g., BitLocker), secure boot chains, attestation for cloud VMs, measured launch of sensitive workloads.
- Security guarantee:
  - The promise is that private keys and certain operations happen inside a hardened module — the module enforces that sensitive material never leaves it in the clear.

---

# Encryption

The process of transforming readable data (_plaintext_) into an unreadable format (_ciphertext_) using a mathematical algorithm and one or more keys.
Its purpose is to protect the confidentiality and integrity of information — ensuring that only authorized parties can access or understand it.

Encryption is broadly divided into two categories: Symmetric and Asymmetric encryption.

## Symmetric Encryption

### Definition

The same key is used for both encryption and decryption.
This means the sender and receiver must both possess the shared secret key beforehand.

Example algorithm - AES.

### Characteristics

- High performance: Fast and efficient, suitable for large amounts of data.
- Challenge: Securely distributing and managing the shared key.
- Best for: Encrypting bulk data, files, or network traffic once keys are established.

### Key Exchange

Since symmetric encryption requires both parties to share a secret key, a secure key exchange mechanism is needed.

Examples:

1. Diffie–Hellman (DH) - parties exchange keys, no other mechanism is required.
2. Using asymetric key - party A creates a symmetric key, sends it encrypted it using public key of party B.

## Asymmetric Encryption

### Definition

Asymmetric encryption uses a key pair:

- A public key (used to encrypt or verify)
- A private key (used to decrypt or sign)

The keys are mathematically related, but the private key cannot be derived from the public key.

Example algorithm - RSA.

### Characteristics

- Public key can be shared openly — private key must be kept secret.
- Slower than symmetric encryption due to heavy math operations.
- Often used to exchange symmetric keys or verify digital signatures, not encrypt large files directly.

### Applications

1. TLS/SSL (HTTPS) –
   Used during the handshake to:

   - Authenticate the server using a certificate.
   - Exchange a symmetric session key securely.
   - Optionally authenticate the client.

2. Digital Signatures –
   The sender signs a message with their private key, and anyone can verify it using the public key.

### How TLS Uses Both

TLS (used by HTTPS) combines both encryption types:

1. Uses asymmetric encryption (RSA or ECDH) for key exchange and authentication.
2. Then switches to symmetric encryption (AES or ChaCha20) for data transfer, since it’s faster.

# TLS / SSL More Information

## Used Files

- `.pem` – a container/encoding (“Privacy-Enhanced Mail”). It’s just Base64 with header/footer lines. A `.pem` can hold a certificate, a private key, a chain (multiple certs), or something else. The extension tells you little; the headers tell you what’s inside:
- `.key` – usually a private key (RSA/EC). Keep secret.
- `.crt` (or `.cer`) – a certificate: public key + identity + issuer + validity, typically X.509. Often PEM-encoded, sometimes DER.

  ```
  -----BEGIN CERTIFICATE-----      (an X.509 cert)
  -----BEGIN PRIVATE KEY-----       (a private key)
  -----BEGIN CERTIFICATE CHAIN----- (bundle)
  ```

Other common extensions you’ll see:

- `.csr` – Certificate Signing Request (you send this to a CA to get a cert).
- `.p12` / `.pfx` – PKCS#12 bundle (can contain key + cert + chain, password-protected).
- `.der` – binary (DER) encoding of a cert or key.

Third party libraries create certificate and key, they should be secure too so key won't be discoverable.

X.509 certificates and private keys are general-purpose public-key materials. They’re used in: TLS/SSL, Code signing, VPNs, Document signing (PDF), etc.

Typical TLS chain on disk:

- `server.key` – server’s private key.
- `server.crt` – server’s certificate (public key + name).
- `chain.pem` or `fullchain.pem` – intermediates up to a trusted root (root is usually on the client, not sent by the server).

## How Trust Works

- Server certificate is signed by a Certificate Authority (CA).
- The client verifies the CA’s digital signature on the server certificate using the CA’s public key from its trust store (root CA, or an intermediate chain up to a trusted root).
- If verification and hostname checks pass, the client trusts the server’s identity.
- During TLS, the server also proves possession of the matching private key (to prevent someone from just presenting a copied cert).
- A self-signed certificate is one where issuer == subject: the certificate is signed by its own private key (no external CA). Used by testing programs and private ecosystems.
- Usually server does not authenticate client because the server does not depend on the client, if it does then the client can have a certificate also.

## Minimal TLS handshake flow (simplified)

1. Client connects, receives server certificate (and chain).
2. Client validates: signature chain → trusted root, validity dates, and hostname/SAN matches.
3. Server proves it owns the private key corresponding to the cert’s public key (via key exchange/signature).
4. They derive symmetric session keys and switch to encrypted traffic.


# Surprising
- Convert string to int - `std::stoi()` | int to string - `std::to_string()`
- Pointer to function - `int (*fp)(int,int)`
- Stream friend function - `friend std::ostream& operator<<(std::ostream& stream, const Buffer& buffer) { return stream << buffer.data; }`
- `std::map` - `ages.insert_or_assign("Tom", 31)`, `ages.at("Tom")`
ages.at("Tom")
- `std::vector` - 
  - Ctor - `std::vector<int> v(10, 0); // (items, initial_value)`
  - find - `auto it = std::find(v.begin(), v.end(), item); if (it == v.end()) { return "Not found"; } `
  - Access items - `.front()`, `.back()`
- Special functions:
  - `__getattr__` - item not found normmally
  - `__getattribute__` - every member every access
  - `__setattr__` - every assignment
- When DNS uses TCP: If the response doesn’t fit in UDP (even with EDNS0) or the server sets TC=1 (Truncated), the client retries over TCP.
- SQL using Cpp:
  ```cpp
  sqlite3* db = nullptr;
  char *query = nullptr;
  char* error = nullptr;
  int result = 0;
  result = sqlite3_open("database.db", &db);
  if (result != SQLITE_OK) { /* error */ }
  query = "QUERY;";
  result = sqlite3_exec(db, query, nullptr, nullptr, &error);
  if (result != SQLITE_OK) { /* error */ }
  sqlite3_close(db);
  ```
- SafeSEH (Safe Structured Exception Handling) restricts exception handler addresses to a validated list in the binary’s load-time table, preventing an attacker from using arbitrary exception handlers to gain control.