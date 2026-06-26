import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.stream.Collectors;
class MyClass {}
public class Test {
    public static void main (String[] args) throws IOException {
        System.out.println("Hello World");
        ArrayList<String> x = new ArrayList<String>();
        x.add("a");
        String[] b = x.toArray(new String[0]);
        System.out.println(b[0]);

        FileReader in = new FileReader("f.txt");
        char c = (char)in.read();

        ArrayList<String> arraylist = new ArrayList<>();
        MyClass[] y = Arrays
                .stream(arraylist.toArray(new MyClass[0]))
                .map(item -> item + "!").toArray(MyClass[]::new);
    }
}