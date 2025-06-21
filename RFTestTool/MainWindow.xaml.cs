using System.Windows;
using System.Net.Sockets;
using System.Threading.Tasks;
using NationalInstruments.Visa; // 需要安装NI-VISA驱动

public partial class MainWindow : Window
{
    private GpibDriver _gpibController;
    private TcpClient _tcpClient;
    private bool _isSampling = false;

    public MainWindow()
    {
        InitializeComponent();
        InitHardware();
    }

    // 硬件初始化
    private void InitHardware()
    {
        // 自动检测GPIB设备
        var rmSession = new ResourceManager();
        var devices = rmSession.Find("GPIB?*");
        Dispatcher.Invoke(() => DeviceList.ItemsSource = devices);
    }

    // TCP/IP连接示例
    private async Task ConnectViaTcp(string ip, int port)
    {
        _tcpClient = new TcpClient();
        await _tcpClient.ConnectAsync(ip, port);
        
        // 启动数据接收线程
        var receiveThread = new Thread(ReceiveDataHandler);
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    // 多线程数据接收
    private void ReceiveDataHandler()
    {
        var stream = _tcpClient.GetStream();
        byte[] buffer = new byte[1024];
        
        while (_isSampling)
        {
            int bytesRead = stream.Read(buffer, 0, buffer.Length);
            var data = Encoding.ASCII.GetString(buffer, 0, bytesRead);
            
            // 更新UI需通过Dispatcher
            Dispatcher.Invoke(() => 
            {
                ChartControl.AddDataPoint(ParseToDataPoint(data));
            });
        }
    }

    // GPIB控制示例
    private void SendGpibCommand(string command)
    {
        using var session = _gpibController.OpenSession("GPIB0::22::INSTR");
        session.Write(command);
        var response = session.ReadString();
        ParseInstrumentResponse(response);
    }

    // 开始测试按钮事件
    private async void StartTest_Click(object sender, RoutedEventArgs e)
    {
        _isSampling = true;
        await Task.Run(() => 
        {
            // 测试逻辑
            SendGpibCommand("FREQ:CENT 1GHz");
            System.Threading.Thread.Sleep(100);
            SendGpibCommand("POW:START -50dBm");
        });
    }
}