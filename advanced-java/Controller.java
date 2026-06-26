import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.ListView;
import javafx.scene.control.TextArea;
import javafx.scene.text.Text;

public class Controller {
    @FXML
    public TextArea textInput;
    @FXML
    private ListView<String> membersView;
    @FXML
    private ListView<String> messagesView;
    @FXML
    private Text userMessage;
    @FXML
    private Button joinButton;

    @FXML void initialize() {
    }

    @FXML
    public void buttonClicked(ActionEvent actionEvent) {
        textInput.setText("");
    }
}
